"""
Pydantic schemas for kiosk operations.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class ClockRequest(BaseModel):
    """Schema for clock-in/out request."""
    clock_code: str = Field(..., min_length=4, max_length=4, pattern=r'^\d{4}$')


class ClockResponse(BaseModel):
    """Schema for clock-in/out response."""
    action: Literal["IN", "OUT"]
    employee_name: str
    timestamp: datetime
