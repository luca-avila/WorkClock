"""
Employee service for business logic operations.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


async def create_employee(
    db: AsyncSession,
    employee_data: EmployeeCreate
) -> Employee:
    """
    Create a new employee.

    Args:
        db: Database session
        employee_data: EmployeeCreate schema with employee details

    Returns:
        Created Employee instance

    Raises:
        HTTPException: 409 if clock code is already in use by an active employee

    Example:
        employee = await create_employee(db, EmployeeCreate(
            name="John Doe",
            job_role="Warehouse Associate",
            daily_rate=Decimal("150.00"),
            clock_code="1234"
        ))
    """
    # Check if clock code is already in use by an active employee
    result = await db.execute(
        select(Employee).where(
            Employee.clock_code == employee_data.clock_code,
            Employee.is_active == True
        )
    )
    existing_employee = result.scalar_one_or_none()

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clock code already in use by an active employee"
        )

    # Create new employee
    employee = Employee(**employee_data.model_dump())
    db.add(employee)
    await db.commit()
    await db.refresh(employee)

    return employee


async def get_employee_by_id(
    db: AsyncSession,
    employee_id: int
) -> Employee:
    """
    Get an employee by ID.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        Employee instance

    Raises:
        HTTPException: 404 if employee not found

    Example:
        employee = await get_employee_by_id(db, 1)
    """
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


async def list_employees(
    db: AsyncSession,
    is_active: bool | None = None
) -> list[Employee]:
    """
    List all employees with optional is_active filter.

    Args:
        db: Database session
        is_active: Optional filter for active/inactive employees

    Returns:
        List of Employee instances (empty list if none found)

    Example:
        # Get all employees
        all_employees = await list_employees(db)

        # Get only active employees
        active_employees = await list_employees(db, is_active=True)

        # Get only inactive employees
        inactive_employees = await list_employees(db, is_active=False)
    """
    query = select(Employee).order_by(Employee.created_at.desc())

    if is_active is not None:
        query = query.where(Employee.is_active == is_active)

    result = await db.execute(query)
    return result.scalars().all()


async def update_employee(
    db: AsyncSession,
    employee_id: int,
    employee_data: EmployeeUpdate
) -> Employee:
    """
    Update an employee's information.

    Args:
        db: Database session
        employee_id: Employee ID
        employee_data: EmployeeUpdate schema with fields to update

    Returns:
        Updated Employee instance

    Raises:
        HTTPException: 404 if employee not found
        HTTPException: 409 if clock code conflicts with another active employee

    Example:
        updated = await update_employee(db, 1, EmployeeUpdate(
            daily_rate=Decimal("175.00")
        ))
    """
    # Get existing employee
    employee = await get_employee_by_id(db, employee_id)

    # If clock code is being updated, check for conflicts and open shifts
    if employee_data.clock_code is not None and employee_data.clock_code != employee.clock_code:
        # Import here to avoid circular dependency
        from app.services.clock_service import get_open_shift_for_employee

        # Check if employee has an open shift
        has_open_shift = await get_open_shift_for_employee(db, employee_id)
        if has_open_shift:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change clock code while employee has an open shift. Employee must clock out first."
            )

        # Check for clock code conflicts with other active employees
        result = await db.execute(
            select(Employee).where(
                Employee.clock_code == employee_data.clock_code,
                Employee.is_active == True,
                Employee.id != employee_id
            )
        )
        conflicting_employee = result.scalar_one_or_none()

        if conflicting_employee:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Clock code already in use by another active employee"
            )

    # Update only provided fields
    update_data = employee_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)

    return employee


async def deactivate_employee(
    db: AsyncSession,
    employee_id: int
) -> Employee:
    """
    Deactivate an employee (soft delete).

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        Deactivated Employee instance

    Raises:
        HTTPException: 404 if employee not found
        HTTPException: 400 if employee is already inactive
        HTTPException: 400 if employee has an open shift

    Example:
        deactivated = await deactivate_employee(db, 1)
    """
    # Import here to avoid circular dependency
    from app.services.clock_service import get_open_shift_for_employee

    # Get employee
    employee = await get_employee_by_id(db, employee_id)

    # Check if already inactive
    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already inactive"
        )

    # Check if employee has an open shift (clocked in but not out)
    has_open_shift = await get_open_shift_for_employee(db, employee_id)
    if has_open_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate employee with an open shift. Employee must clock out first."
        )

    # Deactivate employee
    employee.is_active = False
    await db.commit()
    await db.refresh(employee)

    return employee
