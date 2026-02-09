"""
Clock service - Core business logic for clock-in/out with shift creation.

CRITICAL: This service enforces all 5 core invariants:
1. Clock code uniqueness (active employees only)
2. No double actions (IN→OUT→IN pattern)
3. One open shift per employee
4. Immutable time entries (append-only)
5. Valid IN→OUT pairs for shift creation

All shift creation happens here during clock-out. Shifts are derived state from time_entries.
"""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.models.shift import Shift


async def process_clock_action(
    db: AsyncSession,
    clock_code: str
) -> tuple[TimeEntry, str, str]:
    """
    Single atomic operation for clock-in/out with automatic shift creation.

    This function implements all 5 core invariants in a single database transaction:
    - Validates clock code (Invariant 1)
    - Determines next action based on last entry (Invariants 2 & 3)
    - Creates immutable time entry (Invariant 4)
    - Creates shift if clocking out (Invariant 5)

    Args:
        db: Database session
        clock_code: Employee's 4-digit clock code

    Returns:
        Tuple of (time_entry, action_type, employee_name)
        - time_entry: The created TimeEntry
        - action_type: "IN" or "OUT"
        - employee_name: Employee's name for display

    Raises:
        HTTPException: 400 if clock code is invalid or employee is inactive

    Example:
        # First call with code 1234
        entry, action, name = await process_clock_action(db, "1234")
        # Returns: (TimeEntry, "IN", "John Doe")

        # Second call with same code
        entry, action, name = await process_clock_action(db, "1234")
        # Returns: (TimeEntry, "OUT", "John Doe") + Shift created
    """
    try:
        # 1. Validate clock code and get active employee (Invariant 1)
        employee = await _get_active_employee(db, clock_code)

        # 2. Determine next action based on last entry (Invariants 2 & 3)
        last_entry = await _get_last_time_entry(db, employee.id)
        next_action = _determine_next_action(last_entry)

        # 3. Create immutable time entry (Invariant 4: append-only)
        time_entry = TimeEntry(
            employee_id=employee.id,
            type=next_action,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(time_entry)
        await db.flush()  # Get ID for shift reference

        # 4. If OUT, create shift from valid IN→OUT pair (Invariant 5)
        if next_action == "OUT":
            shift = Shift(
                employee_id=employee.id,
                clock_in_id=last_entry.id,
                clock_out_id=time_entry.id,
                started_at=last_entry.timestamp,
                ended_at=time_entry.timestamp,
                money_gained=employee.daily_rate  # Fixed daily rate
            )
            db.add(shift)

        # 5. Atomic commit: both TimeEntry and Shift (if applicable) succeed together
        await db.commit()
        await db.refresh(time_entry)

        return (time_entry, next_action, employee.name)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        await db.rollback()
        raise
    except Exception as e:
        # Rollback on any unexpected error
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clock action failed: {str(e)}"
        )


async def _get_active_employee(db: AsyncSession, clock_code: str) -> Employee:
    """
    Get active employee by clock code.

    Enforces Invariant 1: Clock code maps to exactly one active employee.

    Args:
        db: Database session
        clock_code: 4-digit clock code

    Returns:
        Active Employee instance

    Raises:
        HTTPException: 400 if code is invalid or employee is inactive
    """
    result = await db.execute(
        select(Employee).where(
            Employee.clock_code == clock_code,
            Employee.is_active == True
        )
    )
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid clock code or employee is inactive"
        )

    return employee


async def _get_last_time_entry(db: AsyncSession, employee_id: int) -> TimeEntry | None:
    """
    Get the most recent time entry for an employee.

    Used to determine the next action (IN or OUT) and for shift creation.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        Most recent TimeEntry or None if no entries exist
    """
    result = await db.execute(
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee_id)
        .order_by(TimeEntry.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _determine_next_action(last_entry: TimeEntry | None) -> str:
    """
    Determine the next clock action based on the last time entry.

    Enforces Invariants 2 & 3:
    - No double clock-in (must alternate IN→OUT→IN)
    - Only one open shift at a time

    Args:
        last_entry: Most recent TimeEntry or None

    Returns:
        "IN" if should clock in, "OUT" if should clock out

    Logic:
        - No entries yet → "IN" (start first shift)
        - Last entry was "IN" → "OUT" (finish open shift)
        - Last entry was "OUT" → "IN" (start new shift)
    """
    if last_entry is None:
        # No previous entries, start with clock in
        return "IN"

    # Alternate: if last was IN, next is OUT, and vice versa
    return "OUT" if last_entry.type == "IN" else "IN"


async def get_open_shift_for_employee(db: AsyncSession, employee_id: int) -> bool:
    """
    Check if an employee has an open shift (clocked in but not out).

    Used by employee_service to prevent deactivating employees with open shifts.

    Args:
        db: Database session
        employee_id: Employee ID

    Returns:
        True if employee has an open shift, False otherwise

    Example:
        has_open_shift = await get_open_shift_for_employee(db, 1)
        if has_open_shift:
            raise HTTPException(400, "Cannot deactivate employee with open shift")
    """
    last_entry = await _get_last_time_entry(db, employee_id)

    # If last entry exists and is type "IN", there's an open shift
    return last_entry is not None and last_entry.type == "IN"
