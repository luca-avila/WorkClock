"""
Tests for kiosk clock-in/out endpoint.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_clock_in_success(client, db_session):
    """Test successful clock in."""
    from app.models.employee import Employee

    employee = Employee(
        name="Test Worker",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9991",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()

    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9991"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "IN"
    assert data["employee_name"] == "Test Worker"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_clock_out_success(client, db_session):
    """Test successful clock out after clock in."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry

    employee = Employee(
        name="Test Worker",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9992",
        is_active=True
    )
    db_session.add(employee)
    await db_session.flush()

    # Create IN entry
    time_entry = TimeEntry(
        employee_id=employee.id,
        type="IN",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(time_entry)
    await db_session.commit()

    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9992"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "OUT"
    assert data["employee_name"] == "Test Worker"


@pytest.mark.asyncio
async def test_clock_invalid_code(client):
    """Test clock action with invalid code returns 400."""
    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9999"}
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_clock_inactive_employee(client, db_session):
    """Test clock action with inactive employee returns 400."""
    from app.models.employee import Employee

    employee = Employee(
        name="Inactive Worker",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9993",
        is_active=False
    )
    db_session.add(employee)
    await db_session.commit()

    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9993"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_clock_creates_shift_on_out(client, db_session):
    """Test that clocking out creates a shift."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from app.models.shift import Shift
    from sqlalchemy import select

    employee = Employee(
        name="Test Worker",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9994",
        is_active=True
    )
    db_session.add(employee)
    await db_session.flush()

    # Create IN entry
    time_entry = TimeEntry(
        employee_id=employee.id,
        type="IN",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(time_entry)
    await db_session.commit()

    # Clock out
    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9994"}
    )

    assert response.status_code == 200

    # Check that shift was created
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee.id)
    )
    shifts = result.scalars().all()
    assert len(shifts) == 1
    assert shifts[0].money_gained == Decimal("150.00")


@pytest.mark.asyncio
async def test_clock_alternating_pattern(client, db_session):
    """Test that clock actions alternate IN -> OUT -> IN -> OUT."""
    from app.models.employee import Employee

    employee = Employee(
        name="Test Worker",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9995",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()

    # First action should be IN
    response1 = await client.post("/kiosk/clock", json={"clock_code": "9995"})
    assert response1.json()["action"] == "IN"

    # Second action should be OUT
    response2 = await client.post("/kiosk/clock", json={"clock_code": "9995"})
    assert response2.json()["action"] == "OUT"

    # Third action should be IN again
    response3 = await client.post("/kiosk/clock", json={"clock_code": "9995"})
    assert response3.json()["action"] == "IN"


@pytest.mark.asyncio
async def test_clock_invalid_format(client):
    """Test clock action with invalid code format returns 422."""
    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "123"}  # Only 3 digits
    )

    assert response.status_code == 422
