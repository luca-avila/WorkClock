"""
Comprehensive tests for the 5 core invariants of WorkClock.

CRITICAL: These tests verify the fundamental business rules that ensure data integrity.
All 5 invariants must pass before the system can be considered production-ready.

The 5 Invariants:
1. Clock code uniqueness - A clock code maps to exactly one active employee
2. No double actions - Cannot clock in twice or clock out without clocking in
3. One open shift - An employee can have only one open shift at a time
4. Immutable entries - Time entries can never be updated or deleted
5. Valid pairs only - Shifts are created only from valid IN → OUT pairs
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.models.employee import Employee
from app.models.time_entry import TimeEntry
from app.models.shift import Shift
from app.services import employee_service, clock_service


# ============================================================================
# INVARIANT 1: Clock Code Uniqueness
# ============================================================================

@pytest.mark.asyncio
async def test_invariant1_clock_code_unique_for_active_employees(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 1: A clock code maps to exactly one active employee.

    Test scenarios:
    1. Create employee with code 1234 - should succeed
    2. Try to create another active employee with code 1234 - should fail with 409
    3. Deactivate first employee
    4. Create new employee with code 1234 - should succeed (code reuse allowed)
    """
    # Scenario 1: Create first employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Employee One",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "1234"
        }
    )
    assert response.status_code == 201
    employee1_id = response.json()["id"]

    # Scenario 2: Try to create duplicate active employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Employee Two",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "1234"  # Same code
        }
    )
    assert response.status_code == 409
    assert "already in use" in response.json()["detail"].lower()

    # Scenario 3: Deactivate first employee
    response = await client.delete(f"/employees/{employee1_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Scenario 4: Now code can be reused
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Employee Two",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "1234"  # Reuse code from inactive employee
        }
    )
    assert response.status_code == 201
    assert response.json()["clock_code"] == "1234"
    assert response.json()["is_active"] is True


@pytest.mark.asyncio
async def test_invariant1_invalid_clock_code_rejected(client: AsyncClient):
    """
    Invariant 1: Invalid clock codes are rejected.

    Test that kiosk endpoint rejects:
    - Non-existent clock codes
    - Inactive employee codes
    """
    # Test non-existent code
    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "9999"}
    )
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invariant1_inactive_employee_cannot_clock(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 1: Inactive employees cannot clock in/out.
    """
    # Create and deactivate employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Inactive Employee",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "5555"
        }
    )
    employee_id = response.json()["id"]

    response = await client.delete(f"/employees/{employee_id}", headers=auth_headers)
    assert response.status_code == 200

    # Try to clock with inactive employee code
    response = await client.post(
        "/kiosk/clock",
        json={"clock_code": "5555"}
    )
    assert response.status_code == 400
    assert "inactive" in response.json()["detail"].lower()


# ============================================================================
# INVARIANT 2: No Double Actions
# ============================================================================

@pytest.mark.asyncio
async def test_invariant2_no_double_clock_in(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 2: Cannot clock in twice without clocking out.

    Test that the system enforces IN → OUT → IN pattern.
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Pattern Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "2222"
        }
    )
    assert response.status_code == 201

    # First action should be IN
    response = await client.post("/kiosk/clock", json={"clock_code": "2222"})
    assert response.status_code == 200
    assert response.json()["action"] == "IN"

    # Second action should be OUT (not another IN)
    response = await client.post("/kiosk/clock", json={"clock_code": "2222"})
    assert response.status_code == 200
    assert response.json()["action"] == "OUT"

    # Third action should be IN again
    response = await client.post("/kiosk/clock", json={"clock_code": "2222"})
    assert response.status_code == 200
    assert response.json()["action"] == "IN"

    # Fourth action should be OUT
    response = await client.post("/kiosk/clock", json={"clock_code": "2222"})
    assert response.status_code == 200
    assert response.json()["action"] == "OUT"


@pytest.mark.asyncio
async def test_invariant2_correct_alternation_pattern(db_session: AsyncSession):
    """
    Invariant 2: Verify IN → OUT → IN → OUT pattern in database.

    Check that time_entries table shows perfect alternation.
    """
    # Create employee directly in database
    employee = Employee(
        name="Alternation Test",
        job_role="Worker",
        daily_rate=Decimal("100.00"),
        clock_code="3333",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    # Perform 4 clock actions
    for expected_action in ["IN", "OUT", "IN", "OUT"]:
        entry, action, _ = await clock_service.process_clock_action(db_session, "3333")
        assert action == expected_action

    # Verify database shows correct pattern
    result = await db_session.execute(
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee.id)
        .order_by(TimeEntry.timestamp)
    )
    entries = result.scalars().all()

    assert len(entries) == 4
    assert entries[0].type == "IN"
    assert entries[1].type == "OUT"
    assert entries[2].type == "IN"
    assert entries[3].type == "OUT"


# ============================================================================
# INVARIANT 3: One Open Shift
# ============================================================================

@pytest.mark.asyncio
async def test_invariant3_only_one_open_shift(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 3: An employee can have only one open shift at a time.

    Test scenarios:
    1. After clock IN, no shift exists (open shift = in-progress)
    2. After clock OUT, exactly one shift exists (closed)
    3. After second clock IN, still only one shift (new one is open)
    4. After second clock OUT, two shifts exist
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Open Shift Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "4444"
        }
    )
    employee_id = response.json()["id"]

    # Scenario 1: Clock IN - no shift should exist yet
    await client.post("/kiosk/clock", json={"clock_code": "4444"})
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shifts = result.scalars().all()
    assert len(shifts) == 0  # Open shift, no closed shift yet

    # Scenario 2: Clock OUT - exactly one shift created
    await client.post("/kiosk/clock", json={"clock_code": "4444"})
    await db_session.commit()  # Ensure we see the new shift
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shifts = result.scalars().all()
    assert len(shifts) == 1  # First shift closed

    # Scenario 3: Clock IN again - still only one closed shift
    await client.post("/kiosk/clock", json={"clock_code": "4444"})
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shifts = result.scalars().all()
    assert len(shifts) == 1  # Second shift is open, not closed yet

    # Scenario 4: Clock OUT - two shifts exist
    await client.post("/kiosk/clock", json={"clock_code": "4444"})
    await db_session.commit()
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shifts = result.scalars().all()
    assert len(shifts) == 2  # Both shifts closed


@pytest.mark.asyncio
async def test_invariant3_cannot_deactivate_with_open_shift(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 3: Cannot deactivate employee with an open shift.

    Employee must clock out before deactivation.
    """
    # Create employee and clock in
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Deactivate Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "6666"
        }
    )
    employee_id = response.json()["id"]

    # Clock in (open shift)
    await client.post("/kiosk/clock", json={"clock_code": "6666"})

    # Try to deactivate - should fail
    response = await client.delete(f"/employees/{employee_id}", headers=auth_headers)
    assert response.status_code == 400
    assert "open shift" in response.json()["detail"].lower()

    # Clock out (close shift)
    await client.post("/kiosk/clock", json={"clock_code": "6666"})

    # Now deactivation should succeed
    response = await client.delete(f"/employees/{employee_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ============================================================================
# INVARIANT 4: Immutable Entries
# ============================================================================

@pytest.mark.asyncio
async def test_invariant4_time_entries_are_immutable(db_session: AsyncSession):
    """
    Invariant 4: Time entries can never be updated or deleted.

    Verify that:
    1. No update methods exist in the service
    2. Time entries persist even after shifts are created
    3. Complete audit trail is maintained
    """
    # Create employee
    employee = Employee(
        name="Immutable Test",
        job_role="Worker",
        daily_rate=Decimal("100.00"),
        clock_code="7777",
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)

    # Create multiple clock actions
    await clock_service.process_clock_action(db_session, "7777")  # IN
    await clock_service.process_clock_action(db_session, "7777")  # OUT
    await clock_service.process_clock_action(db_session, "7777")  # IN
    await clock_service.process_clock_action(db_session, "7777")  # OUT

    # Verify all 4 time entries still exist
    result = await db_session.execute(
        select(TimeEntry).where(TimeEntry.employee_id == employee.id)
    )
    entries = result.scalars().all()
    assert len(entries) == 4

    # Verify entries are in chronological order and unchanged
    for i in range(len(entries) - 1):
        assert entries[i].timestamp <= entries[i + 1].timestamp

    # Verify no update capability exists
    assert not hasattr(clock_service, 'update_time_entry')
    assert not hasattr(clock_service, 'delete_time_entry')


@pytest.mark.asyncio
async def test_invariant4_complete_audit_trail(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 4: Complete audit trail maintained.

    All clock actions are recorded and preserved.
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Audit Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "8888"
        }
    )
    employee_id = response.json()["id"]

    # Perform multiple clock actions
    actions_performed = []
    for _ in range(6):  # 3 complete shifts
        response = await client.post("/kiosk/clock", json={"clock_code": "8888"})
        actions_performed.append(response.json()["action"])

    # Verify audit trail
    result = await db_session.execute(
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee_id)
        .order_by(TimeEntry.timestamp)
    )
    entries = result.scalars().all()

    assert len(entries) == 6
    for i, entry in enumerate(entries):
        assert entry.type == actions_performed[i]


# ============================================================================
# INVARIANT 5: Valid Pairs Only
# ============================================================================

@pytest.mark.asyncio
async def test_invariant5_shifts_created_only_from_valid_pairs(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 5: Shifts are created only from valid IN → OUT pairs.

    Test that:
    1. Shift is created only on OUT action
    2. Shift references correct IN and OUT time entries
    3. money_gained equals employee daily_rate at shift creation
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Valid Pair Test",
            "job_role": "Worker",
            "daily_rate": "150.00",
            "clock_code": "1111"
        }
    )
    employee_id = response.json()["id"]

    # Clock IN - no shift should be created
    await client.post("/kiosk/clock", json={"clock_code": "1111"})
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    assert len(result.scalars().all()) == 0

    # Clock OUT - shift should be created
    await client.post("/kiosk/clock", json={"clock_code": "1111"})
    await db_session.commit()

    # Verify shift was created with valid references
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shift = result.scalar_one()

    # Get the time entries
    result = await db_session.execute(
        select(TimeEntry)
        .where(TimeEntry.employee_id == employee_id)
        .order_by(TimeEntry.timestamp)
    )
    entries = result.scalars().all()

    # Verify valid IN → OUT pair
    assert len(entries) == 2
    assert entries[0].type == "IN"
    assert entries[1].type == "OUT"

    # Verify shift references
    assert shift.clock_in_id == entries[0].id
    assert shift.clock_out_id == entries[1].id
    assert shift.started_at == entries[0].timestamp
    assert shift.ended_at == entries[1].timestamp

    # Verify payment
    assert shift.money_gained == Decimal("150.00")


@pytest.mark.asyncio
async def test_invariant5_shift_payment_uses_daily_rate_at_creation(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 5: Shift payment is employee's daily_rate at shift creation time.

    Test that money_gained is set correctly even if daily_rate changes later.
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Payment Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "0001"
        }
    )
    employee_id = response.json()["id"]

    # Complete first shift
    await client.post("/kiosk/clock", json={"clock_code": "0001"})  # IN
    await client.post("/kiosk/clock", json={"clock_code": "0001"})  # OUT
    await db_session.commit()

    # Change employee daily_rate
    response = await client.patch(
        f"/employees/{employee_id}",
        headers=auth_headers,
        json={"daily_rate": "200.00"}
    )
    assert response.status_code == 200

    # Complete second shift
    await client.post("/kiosk/clock", json={"clock_code": "0001"})  # IN
    await client.post("/kiosk/clock", json={"clock_code": "0001"})  # OUT
    await db_session.commit()

    # Verify both shifts have correct payment
    result = await db_session.execute(
        select(Shift)
        .where(Shift.employee_id == employee_id)
        .order_by(Shift.started_at)
    )
    shifts = result.scalars().all()

    assert len(shifts) == 2
    assert shifts[0].money_gained == Decimal("100.00")  # Old rate
    assert shifts[1].money_gained == Decimal("200.00")  # New rate


@pytest.mark.asyncio
async def test_invariant5_shift_timestamps_match_time_entries(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Invariant 5: Shift timestamps match referenced time entries exactly.
    """
    # Create employee
    response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Timestamp Test",
            "job_role": "Worker",
            "daily_rate": "100.00",
            "clock_code": "0002"
        }
    )
    employee_id = response.json()["id"]

    # Complete shift
    await client.post("/kiosk/clock", json={"clock_code": "0002"})  # IN
    await client.post("/kiosk/clock", json={"clock_code": "0002"})  # OUT
    await db_session.commit()

    # Get shift
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == employee_id)
    )
    shift = result.scalar_one()

    # Get referenced time entries
    result = await db_session.execute(
        select(TimeEntry).where(TimeEntry.id == shift.clock_in_id)
    )
    clock_in_entry = result.scalar_one()

    result = await db_session.execute(
        select(TimeEntry).where(TimeEntry.id == shift.clock_out_id)
    )
    clock_out_entry = result.scalar_one()

    # Verify exact timestamp match
    assert shift.started_at == clock_in_entry.timestamp
    assert shift.ended_at == clock_out_entry.timestamp
    assert shift.ended_at > shift.started_at


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_all_invariants_together(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_headers: dict
):
    """
    Integration test: All 5 invariants working together.

    Simulates real-world usage with multiple employees and shifts.
    """
    # Create two employees
    emp1_response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Alice",
            "job_role": "Worker A",
            "daily_rate": "120.00",
            "clock_code": "0101"
        }
    )
    emp1_id = emp1_response.json()["id"]

    emp2_response = await client.post(
        "/employees",
        headers=auth_headers,
        json={
            "name": "Bob",
            "job_role": "Worker B",
            "daily_rate": "130.00",
            "clock_code": "0202"
        }
    )
    emp2_id = emp2_response.json()["id"]

    # Simulate work day
    # Alice clocks in
    response = await client.post("/kiosk/clock", json={"clock_code": "0101"})
    assert response.json()["action"] == "IN"

    # Bob clocks in
    response = await client.post("/kiosk/clock", json={"clock_code": "0202"})
    assert response.json()["action"] == "IN"

    # Alice clocks out
    response = await client.post("/kiosk/clock", json={"clock_code": "0101"})
    assert response.json()["action"] == "OUT"

    # Bob clocks out
    response = await client.post("/kiosk/clock", json={"clock_code": "0202"})
    assert response.json()["action"] == "OUT"

    await db_session.commit()

    # Verify results
    result = await db_session.execute(select(Shift))
    all_shifts = result.scalars().all()
    assert len(all_shifts) == 2

    result = await db_session.execute(select(TimeEntry))
    all_entries = result.scalars().all()
    assert len(all_entries) == 4

    # Verify each employee has correct shift payment
    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == emp1_id)
    )
    alice_shift = result.scalar_one()
    assert alice_shift.money_gained == Decimal("120.00")

    result = await db_session.execute(
        select(Shift).where(Shift.employee_id == emp2_id)
    )
    bob_shift = result.scalar_one()
    assert bob_shift.money_gained == Decimal("130.00")
