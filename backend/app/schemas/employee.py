"""
Pydantic schemas for employee operations.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from decimal import Decimal


class EmployeeBase(BaseModel):
    """Base employee schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    job_role: str = Field(..., min_length=1, max_length=255)
    daily_rate: Decimal = Field(..., gt=0, decimal_places=2)
    clock_code: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')

    @field_validator('clock_code')
    @classmethod
    def validate_clock_code(cls, v: str) -> str:
        """Ensure clock code is exactly 4 digits."""
        if not v.isdigit() or len(v) != 4:
            raise ValueError('Clock code must be exactly 4 digits')
        return v


class EmployeeCreate(EmployeeBase):
    """Schema for creating a new employee."""
    pass


class EmployeeUpdate(BaseModel):
    """Schema for updating an employee (all fields optional)."""
    name: str | None = Field(None, min_length=1, max_length=255)
    job_role: str | None = Field(None, min_length=1, max_length=255)
    daily_rate: Decimal | None = Field(None, gt=0, decimal_places=2)
    clock_code: str | None = Field(None, min_length=4, max_length=4, pattern=r'^\d{4}$')
    is_active: bool | None = None

    @field_validator('clock_code')
    @classmethod
    def validate_clock_code(cls, v: str | None) -> str | None:
        """Ensure clock code is exactly 4 digits if provided."""
        if v is not None and (not v.isdigit() or len(v) != 4):
            raise ValueError('Clock code must be exactly 4 digits')
        return v


class EmployeeResponse(EmployeeBase):
    """Schema for employee response."""
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
