"""
Tests for employee management endpoints.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_employee_success(auth_headers):
    """Test creating a new employee with valid data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/employees",
            json={
                "name": "Jane Doe",
                "job_role": "Forklift Operator",
                "daily_rate": "175.00",
                "clock_code": "5678"
            },
            headers=auth_headers
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["job_role"] == "Forklift Operator"
    assert data["daily_rate"] == "175.00"
    assert data["clock_code"] == "5678"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_employee_duplicate_code(db_session, auth_headers):
    """Test creating employee with duplicate clock code returns 409."""
    from app.models.employee import Employee

    # Create first employee
    employee = Employee(
        name="First Employee",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="1111",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()

    # Try to create second employee with same code
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/employees",
            json={
                "name": "Second Employee",
                "job_role": "Worker",
                "daily_rate": "160.00",
                "clock_code": "1111"
            },
            headers=auth_headers
        )

    assert response.status_code == 409
    assert "already in use" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_employee_invalid_clock_code(auth_headers):
    """Test creating employee with invalid clock code returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Clock code with only 3 digits
        response = await client.post(
            "/employees",
            json={
                "name": "Jane Doe",
                "job_role": "Worker",
                "daily_rate": "150.00",
                "clock_code": "123"  # Only 3 digits
            },
            headers=auth_headers
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_employee_negative_rate(auth_headers):
    """Test creating employee with negative daily rate returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/employees",
            json={
                "name": "Jane Doe",
                "job_role": "Worker",
                "daily_rate": "-50.00",  # Negative
                "clock_code": "1234"
            },
            headers=auth_headers
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_employees_all(db_session, auth_headers):
    """Test listing all employees."""
    from app.models.employee import Employee

    # Create test employees
    employees = [
        Employee(name="Active 1", job_role="Worker", daily_rate=Decimal("150"), clock_code="2001", is_active=True),
        Employee(name="Active 2", job_role="Worker", daily_rate=Decimal("160"), clock_code="2002", is_active=True),
        Employee(name="Inactive 1", job_role="Worker", daily_rate=Decimal("170"), clock_code="2003", is_active=False),
    ]
    for emp in employees:
        db_session.add(emp)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/employees", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_list_employees_active_only(db_session, auth_headers):
    """Test listing only active employees."""
    from app.models.employee import Employee

    # Create test employees
    employees = [
        Employee(name="Active", job_role="Worker", daily_rate=Decimal("150"), clock_code="3001", is_active=True),
        Employee(name="Inactive", job_role="Worker", daily_rate=Decimal("160"), clock_code="3002", is_active=False),
    ]
    for emp in employees:
        db_session.add(emp)
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/employees?is_active=true", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert all(emp["is_active"] is True for emp in data)


@pytest.mark.asyncio
async def test_get_employee_by_id(db_session, auth_headers):
    """Test getting a single employee by ID."""
    from app.models.employee import Employee

    employee = Employee(
        name="Test Employee",
        job_role="Tester",
        daily_rate=Decimal("175.00"),
        clock_code="4001",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/employees/{employee.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == employee.id
    assert data["name"] == "Test Employee"


@pytest.mark.asyncio
async def test_get_employee_not_found(auth_headers):
    """Test getting non-existent employee returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/employees/99999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_employee_success(db_session, auth_headers):
    """Test updating an employee."""
    from app.models.employee import Employee

    employee = Employee(
        name="Original Name",
        job_role="Original Role",
        daily_rate=Decimal("150.00"),
        clock_code="5001",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/employees/{employee.id}",
            json={"name": "Updated Name", "daily_rate": "200.00"},
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["daily_rate"] == "200.00"
    assert data["job_role"] == "Original Role"  # Unchanged


@pytest.mark.asyncio
async def test_update_employee_clock_code_conflict(db_session, auth_headers):
    """Test updating clock code to one already in use returns 409."""
    from app.models.employee import Employee

    emp1 = Employee(name="Emp 1", job_role="Worker", daily_rate=Decimal("150"), clock_code="6001", is_active=True)
    emp2 = Employee(name="Emp 2", job_role="Worker", daily_rate=Decimal("160"), clock_code="6002", is_active=True)
    db_session.add_all([emp1, emp2])
    await db_session.commit()
    await db_session.refresh(emp2)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch(
            f"/employees/{emp2.id}",
            json={"clock_code": "6001"},  # Try to use emp1's code
            headers=auth_headers
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_deactivate_employee_success(db_session, auth_headers):
    """Test deactivating an active employee."""
    from app.models.employee import Employee

    employee = Employee(
        name="To Deactivate",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="7001",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/employees/{employee.id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_deactivate_already_inactive(db_session, auth_headers):
    """Test deactivating an already inactive employee returns 400."""
    from app.models.employee import Employee

    employee = Employee(
        name="Already Inactive",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="8001",
        is_active=False
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/employees/{employee.id}", headers=auth_headers)

    assert response.status_code == 400
    assert "already inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deactivate_with_open_shift(db_session, auth_headers):
    """Test deactivating employee with open shift returns 400."""
    from app.models.employee import Employee
    from app.models.time_entry import TimeEntry
    from datetime import datetime, timezone

    employee = Employee(
        name="Has Open Shift",
        job_role="Worker",
        daily_rate=Decimal("150.00"),
        clock_code="9001",
        is_active=True
    )
    db_session.add(employee)
    await db_session.flush()

    # Create an IN entry (open shift)
    time_entry = TimeEntry(
        employee_id=employee.id,
        type="IN",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(time_entry)
    await db_session.commit()
    await db_session.refresh(employee)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/employees/{employee.id}", headers=auth_headers)

    assert response.status_code == 400
    assert "open shift" in response.json()["detail"].lower()
