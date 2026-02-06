"""
Pydantic schemas for shift operations.
"""
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ShiftResponse(BaseModel):
    """Schema for shift response."""
    id: int
    employee_id: int
    clock_in_id: int
    clock_out_id: int
    started_at: datetime
    ended_at: datetime
    money_gained: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}


class ShiftWithEmployee(ShiftResponse):
    """Schema for shift with employee details."""
    employee_name: str


class ShiftListResponse(BaseModel):
    """Schema for paginated shift list."""
    shifts: list[ShiftWithEmployee]
    total: int


class MonthlyEmployeeReport(BaseModel):
    """Schema for employee's monthly report."""
    employee_id: int
    employee_name: str
    total_shifts: int
    total_payment: Decimal


class MonthlyReport(BaseModel):
    """Schema for complete monthly report."""
    month: str  # Format: YYYY-MM
    employees: list[MonthlyEmployeeReport]
    grand_total: Decimal
