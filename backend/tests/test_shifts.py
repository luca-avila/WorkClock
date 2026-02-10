"""
Tests for shift reporting endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from decimal import Decimal
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_list_shifts_empty(auth_headers):
    """Test listing shifts when none exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "shifts" in data
    assert "total" in data
    assert isinstance(data["shifts"], list)


@pytest.mark.asyncio
async def test_list_shifts_with_data(db_session, auth_headers):
    """Test listing shifts with data."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from app.models.shift import Shift

    # Create employee
    employee = Employee(
        name="Worker",
        job_role="Tester",
        daily_rate=Decimal("150.00"),
        clock_code="1111",
        is_active=True
    )
    db_session.add(employee)
    await db_session.flush()

    # Create time entries and shift
    now = datetime.now(timezone.utc)
    in_entry = TimeEntry(employee_id=employee.id, type="IN", timestamp=now)
    out_entry = TimeEntry(employee_id=employee.id, type="OUT", timestamp=now + timedelta(hours=8))
    db_session.add_all([in_entry, out_entry])
    await db_session.flush()

    shift = Shift(
        employee_id=employee.id,
        clock_in_id=in_entry.id,
        clock_out_id=out_entry.id,
        started_at=now,
        ended_at=now + timedelta(hours=8),
        money_gained=Decimal("150.00")
    )
    db_session.add(shift)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["shifts"]) >= 1
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_shifts_filter_by_employee(db_session, auth_headers):
    """Test filtering shifts by employee ID."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from app.models.shift import Shift

    # Create two employees
    emp1 = Employee(name="Emp 1", job_role="Worker", daily_rate=Decimal("150"), clock_code="2001", is_active=True)
    emp2 = Employee(name="Emp 2", job_role="Worker", daily_rate=Decimal("160"), clock_code="2002", is_active=True)
    db_session.add_all([emp1, emp2])
    await db_session.flush()

    # Create shifts for both
    now = datetime.now(timezone.utc)
    for emp in [emp1, emp2]:
        in_entry = TimeEntry(employee_id=emp.id, type="IN", timestamp=now)
        out_entry = TimeEntry(employee_id=emp.id, type="OUT", timestamp=now + timedelta(hours=8))
        db_session.add_all([in_entry, out_entry])
        await db_session.flush()

        shift = Shift(
            employee_id=emp.id,
            clock_in_id=in_entry.id,
            clock_out_id=out_entry.id,
            started_at=now,
            ended_at=now + timedelta(hours=8),
            money_gained=emp.daily_rate
        )
        db_session.add(shift)

    await db_session.commit()
    await db_session.refresh(emp1)

    # Filter by emp1
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/shifts?employee_id={emp1.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(shift["employee_id"] == emp1.id for shift in data["shifts"])


@pytest.mark.asyncio
async def test_list_shifts_pagination(db_session, auth_headers):
    """Test shift list pagination."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from app.models.shift import Shift

    # Create employee
    employee = Employee(name="Worker", job_role="Worker", daily_rate=Decimal("150"), clock_code="3001", is_active=True)
    db_session.add(employee)
    await db_session.flush()

    # Create multiple shifts
    now = datetime.now(timezone.utc)
    for i in range(5):
        shift_time = now + timedelta(days=i)
        in_entry = TimeEntry(employee_id=employee.id, type="IN", timestamp=shift_time)
        out_entry = TimeEntry(employee_id=employee.id, type="OUT", timestamp=shift_time + timedelta(hours=8))
        db_session.add_all([in_entry, out_entry])
        await db_session.flush()

        shift = Shift(
            employee_id=employee.id,
            clock_in_id=in_entry.id,
            clock_out_id=out_entry.id,
            started_at=shift_time,
            ended_at=shift_time + timedelta(hours=8),
            money_gained=Decimal("150.00")
        )
        db_session.add(shift)

    await db_session.commit()

    # Test pagination
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts?limit=2&offset=0", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["shifts"]) <= 2


@pytest.mark.asyncio
async def test_monthly_report_empty(auth_headers):
    """Test monthly report with no data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts/monthly-report?year=2026&month=1", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "month" in data
    assert "employees" in data
    assert "grand_total" in data


@pytest.mark.asyncio
async def test_monthly_report_with_data(db_session, auth_headers):
    """Test monthly report with shift data."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from app.models.shift import Shift

    # Create employee
    employee = Employee(name="Worker", job_role="Worker", daily_rate=Decimal("150"), clock_code="4001", is_active=True)
    db_session.add(employee)
    await db_session.flush()

    # Create shifts in current month
    now = datetime.now(timezone.utc)
    for i in range(3):
        shift_time = now + timedelta(days=i)
        in_entry = TimeEntry(employee_id=employee.id, type="IN", timestamp=shift_time)
        out_entry = TimeEntry(employee_id=employee.id, type="OUT", timestamp=shift_time + timedelta(hours=8))
        db_session.add_all([in_entry, out_entry])
        await db_session.flush()

        shift = Shift(
            employee_id=employee.id,
            clock_in_id=in_entry.id,
            clock_out_id=out_entry.id,
            started_at=shift_time,
            ended_at=shift_time + timedelta(hours=8),
            money_gained=Decimal("150.00")
        )
        db_session.add(shift)

    await db_session.commit()

    # Get report for current month
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/shifts/monthly-report?year={now.year}&month={now.month}",
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["employees"]) >= 1
    assert float(data["grand_total"]) >= 450.00  # 3 shifts * 150


@pytest.mark.asyncio
async def test_monthly_report_invalid_month(auth_headers):
    """Test monthly report with invalid month returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts/monthly-report?year=2026&month=13", headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shifts_requires_auth():
    """Test that shifts endpoints require authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/shifts")

    assert response.status_code == 401
