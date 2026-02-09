"""
Employee router for CRUD operations.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services import employee_service

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(get_current_admin)]  # All endpoints require admin authentication
)


@router.get("", response_model=list[EmployeeResponse])
async def list_employees(
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db)
) -> list[EmployeeResponse]:
    """
    List all employees with optional is_active filter.

    Query Parameters:
        is_active: Optional filter for active/inactive employees
            - None: Return all employees
            - True: Return only active employees
            - False: Return only inactive employees

    Returns:
        List of employees (empty list if none found)

    Example Request:
        GET /employees
        GET /employees?is_active=true
        GET /employees?is_active=false

    Example Response:
        [
            {
                "id": 1,
                "name": "John Doe",
                "job_role": "Warehouse Associate",
                "daily_rate": "150.00",
                "clock_code": "1234",
                "is_active": true,
                "created_at": "2025-01-15T10:00:00Z"
            }
        ]
    """
    employees = await employee_service.list_employees(db, is_active)
    return employees


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db)
) -> EmployeeResponse:
    """
    Create a new employee.

    Request Body:
        EmployeeCreate schema with employee details

    Returns:
        Created employee data

    Raises:
        HTTPException: 409 if clock code is already in use by an active employee
        HTTPException: 422 if validation fails (invalid fields)

    Example Request:
        POST /employees
        {
            "name": "John Doe",
            "job_role": "Warehouse Associate",
            "daily_rate": "150.00",
            "clock_code": "1234"
        }

    Example Response:
        {
            "id": 1,
            "name": "John Doe",
            "job_role": "Warehouse Associate",
            "daily_rate": "150.00",
            "clock_code": "1234",
            "is_active": true,
            "created_at": "2025-01-15T10:00:00Z"
        }
    """
    employee = await employee_service.create_employee(db, employee_data)
    return employee


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db)
) -> EmployeeResponse:
    """
    Get a single employee by ID.

    Path Parameters:
        employee_id: Employee ID

    Returns:
        Employee data

    Raises:
        HTTPException: 404 if employee not found

    Example Request:
        GET /employees/1

    Example Response:
        {
            "id": 1,
            "name": "John Doe",
            "job_role": "Warehouse Associate",
            "daily_rate": "150.00",
            "clock_code": "1234",
            "is_active": true,
            "created_at": "2025-01-15T10:00:00Z"
        }
    """
    employee = await employee_service.get_employee_by_id(db, employee_id)
    return employee


@router.patch("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db)
) -> EmployeeResponse:
    """
    Update an employee's information.

    All fields are optional - only provided fields will be updated.

    Path Parameters:
        employee_id: Employee ID

    Request Body:
        EmployeeUpdate schema with fields to update

    Returns:
        Updated employee data

    Raises:
        HTTPException: 404 if employee not found
        HTTPException: 409 if clock code conflicts with another active employee
        HTTPException: 422 if validation fails

    Example Request:
        PATCH /employees/1
        {
            "daily_rate": "175.00"
        }

    Example Response:
        {
            "id": 1,
            "name": "John Doe",
            "job_role": "Warehouse Associate",
            "daily_rate": "175.00",
            "clock_code": "1234",
            "is_active": true,
            "created_at": "2025-01-15T10:00:00Z"
        }
    """
    employee = await employee_service.update_employee(db, employee_id, employee_data)
    return employee


@router.delete("/{employee_id}", response_model=EmployeeResponse)
async def deactivate_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db)
) -> EmployeeResponse:
    """
    Deactivate an employee (soft delete).

    Sets is_active to false. The employee record remains in the database.
    After deactivation, the clock code can be reused by a new employee.

    Path Parameters:
        employee_id: Employee ID

    Returns:
        Deactivated employee data

    Raises:
        HTTPException: 404 if employee not found
        HTTPException: 400 if employee is already inactive

    Example Request:
        DELETE /employees/1

    Example Response:
        {
            "id": 1,
            "name": "John Doe",
            "job_role": "Warehouse Associate",
            "daily_rate": "150.00",
            "clock_code": "1234",
            "is_active": false,
            "created_at": "2025-01-15T10:00:00Z"
        }
    """
    employee = await employee_service.deactivate_employee(db, employee_id)
    return employee
