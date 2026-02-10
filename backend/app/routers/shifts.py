"""
Shifts router for reporting and analytics.

All endpoints are read-only and require admin authentication.
Shifts are created automatically by ClockService on clock-out.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.shift import ShiftWithEmployee, ShiftListResponse, MonthlyReport, MonthlyEmployeeReport
from app.services import shift_service

router = APIRouter(
    prefix="/shifts",
    tags=["shifts"],
    dependencies=[Depends(get_current_admin)]  # All endpoints require admin auth
)


@router.get("", response_model=ShiftListResponse)
async def list_shifts(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
) -> ShiftListResponse:
    """
    List shifts with optional filters and pagination.

    Query Parameters:
        employee_id: Filter by employee (optional)
        start_date: Filter by start date in YYYY-MM-DD format (optional)
        end_date: Filter by end date in YYYY-MM-DD format (optional)
        limit: Maximum results to return (1-100, default 50)
        offset: Number of results to skip for pagination (default 0)

    Returns:
        ShiftListResponse with shifts array and total count

    Example Request:
        GET /shifts?employee_id=1&start_date=2026-02-01&end_date=2026-02-28&limit=20&offset=0

    Example Response:
        {
            "shifts": [
                {
                    "id": 1,
                    "employee_id": 1,
                    "employee_name": "John Doe",
                    "clock_in_id": 1,
                    "clock_out_id": 2,
                    "started_at": "2026-02-09T14:00:00Z",
                    "ended_at": "2026-02-09T22:00:00Z",
                    "money_gained": "150.00",
                    "created_at": "2026-02-09T22:00:00Z"
                }
            ],
            "total": 45
        }
    """
    # Parse dates if provided
    # For end_date, add 1 day to include the entire selected day (inclusive)
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) + timedelta(days=1) if end_date else None

    # Get shifts
    shifts, total = await shift_service.list_shifts(
        db,
        employee_id=employee_id,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset
    )

    # Convert to response format
    shift_responses = [
        ShiftWithEmployee(
            id=shift.id,
            employee_id=shift.employee_id,
            employee_name=shift.employee.name,
            clock_in_id=shift.clock_in_id,
            clock_out_id=shift.clock_out_id,
            started_at=shift.started_at,
            ended_at=shift.ended_at,
            money_gained=shift.money_gained,
            created_at=shift.created_at
        )
        for shift in shifts
    ]

    return ShiftListResponse(shifts=shift_responses, total=total)


@router.get("/monthly-report", response_model=MonthlyReport)
async def get_monthly_report(
    year: int = Query(..., ge=2000, le=2100, description="Year (e.g., 2026)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: AsyncSession = Depends(get_db)
) -> MonthlyReport:
    """
    Generate monthly payment report for all employees.

    Groups shifts by employee for the specified month and calculates totals.

    Query Parameters:
        year: Year (2000-2100)
        month: Month (1-12)

    Returns:
        MonthlyReport with employee summaries and grand total

    Example Request:
        GET /shifts/monthly-report?year=2026&month=2

    Example Response:
        {
            "month": "2026-02",
            "employees": [
                {
                    "employee_id": 1,
                    "employee_name": "John Doe",
                    "total_shifts": 20,
                    "total_payment": "3000.00"
                },
                {
                    "employee_id": 2,
                    "employee_name": "Jane Smith",
                    "total_shifts": 18,
                    "total_payment": "2700.00"
                }
            ],
            "grand_total": "5700.00"
        }
    """
    # Get employee reports
    employee_reports = await shift_service.get_monthly_report(db, year, month)

    # Calculate grand total
    grand_total = sum(emp['total_payment'] for emp in employee_reports)

    # Convert to response format
    employees = [
        MonthlyEmployeeReport(
            employee_id=emp['employee_id'],
            employee_name=emp['employee_name'],
            total_shifts=emp['total_shifts'],
            total_payment=Decimal(str(emp['total_payment']))
        )
        for emp in employee_reports
    ]

    return MonthlyReport(
        month=f"{year:04d}-{month:02d}",
        employees=employees,
        grand_total=Decimal(str(grand_total))
    )
