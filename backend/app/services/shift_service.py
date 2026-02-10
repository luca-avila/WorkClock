"""
Shift service - Read-only queries for shift reporting.

IMPORTANT: Shifts are ONLY created by ClockService during clock-out.
This service provides read operations for reporting and analytics.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.shift import Shift
from app.models.employee import Employee


async def list_shifts(
    db: AsyncSession,
    employee_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[Shift], int]:
    """
    List shifts with optional filters and pagination.

    Args:
        db: Database session
        employee_id: Optional filter by employee ID
        start_date: Optional filter by start date (inclusive)
        end_date: Optional filter by end date (inclusive)
        limit: Maximum number of results (default 50)
        offset: Number of results to skip (default 0)

    Returns:
        Tuple of (shifts list, total count)

    Example:
        shifts, total = await list_shifts(
            db,
            employee_id=1,
            start_date=datetime(2026, 2, 1),
            end_date=datetime(2026, 2, 28),
            limit=20,
            offset=0
        )
    """
    # Build query with filters
    query = select(Shift).options(joinedload(Shift.employee))

    filters = []
    if employee_id is not None:
        filters.append(Shift.employee_id == employee_id)
    if start_date is not None:
        filters.append(Shift.started_at >= start_date)
    if end_date is not None:
        filters.append(Shift.ended_at <= end_date)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Shift)
    if filters:
        count_query = count_query.where(and_(*filters))
    result = await db.execute(count_query)
    total = result.scalar()

    # Get paginated results
    query = query.order_by(Shift.started_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    shifts = result.scalars().all()

    return shifts, total


async def get_monthly_report(
    db: AsyncSession,
    year: int,
    month: int
) -> list[dict]:
    """
    Generate monthly payment report for all employees.

    Args:
        db: Database session
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        List of employee payment summaries:
        [
            {
                "employee_id": 1,
                "employee_name": "John Doe",
                "total_shifts": 20,
                "total_payment": 3000.00
            },
            ...
        ]

    Example:
        report = await get_monthly_report(db, 2026, 2)
    """
    # Calculate month boundaries
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Query: Group by employee, sum money_gained
    query = (
        select(
            Employee.id.label('employee_id'),
            Employee.name.label('employee_name'),
            func.count(Shift.id).label('total_shifts'),
            func.sum(Shift.money_gained).label('total_payment')
        )
        .select_from(Shift)
        .join(Employee, Shift.employee_id == Employee.id)
        .where(
            and_(
                Shift.started_at >= start_date,
                Shift.started_at < end_date
            )
        )
        .group_by(Employee.id, Employee.name)
        .order_by(Employee.name)
    )

    result = await db.execute(query)
    rows = result.all()

    # Convert to list of dicts
    return [
        {
            'employee_id': row.employee_id,
            'employee_name': row.employee_name,
            'total_shifts': row.total_shifts,
            'total_payment': float(row.total_payment) if row.total_payment else 0.0
        }
        for row in rows
    ]
