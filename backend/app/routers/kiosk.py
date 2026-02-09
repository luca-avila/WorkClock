"""
Kiosk router for employee clock-in/out operations.

Public endpoint (no authentication required) for kiosk terminals.
Employees use 4-digit PIN codes to clock in and out.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.kiosk import ClockRequest, ClockResponse
from app.services import clock_service

router = APIRouter(
    prefix="/kiosk",
    tags=["kiosk"]
    # No authentication dependency - kiosk is public
)


@router.post("/clock", response_model=ClockResponse)
async def clock_action(
    request: ClockRequest,
    db: AsyncSession = Depends(get_db)
) -> ClockResponse:
    """
    Process employee clock-in or clock-out action.

    This is the main kiosk endpoint used by employees to:
    - Clock IN: Start a new shift
    - Clock OUT: End current shift and create shift record

    The system automatically determines whether to clock in or out based on
    the employee's last action. Shifts are created automatically on clock-out.

    **No authentication required** - employees use 4-digit PIN codes.

    Request Body:
        clock_code: 4-digit employee PIN code

    Returns:
        ClockResponse with action taken, employee name, and timestamp

    Raises:
        HTTPException: 400 if clock code is invalid or employee is inactive
        HTTPException: 500 if an unexpected error occurs

    Example Request:
        POST /kiosk/clock
        {
            "clock_code": "1234"
        }

    Example Response (Clock IN):
        {
            "action": "IN",
            "employee_name": "John Doe",
            "timestamp": "2026-02-09T14:30:00Z"
        }

    Example Response (Clock OUT):
        {
            "action": "OUT",
            "employee_name": "John Doe",
            "timestamp": "2026-02-09T22:45:00Z"
        }

    Business Logic:
        1. Validate clock code (must be active employee)
        2. Check last action (IN or OUT)
        3. Perform opposite action (OUT if last was IN, IN if last was OUT)
        4. If OUT, automatically create shift record with payment
        5. Return confirmation to display on kiosk

    Invariants Enforced:
        - Invariant 1: Clock code must belong to an active employee
        - Invariant 2: No double clock-in (alternates IN→OUT→IN)
        - Invariant 3: One open shift per employee
        - Invariant 4: Time entries are immutable (append-only)
        - Invariant 5: Shifts created only from valid IN→OUT pairs
    """
    # Delegate all business logic to ClockService
    time_entry, action, employee_name = await clock_service.process_clock_action(
        db, request.clock_code
    )

    return ClockResponse(
        action=action,
        employee_name=employee_name,
        timestamp=time_entry.timestamp
    )
