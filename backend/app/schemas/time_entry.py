"""
Pydantic schemas for time entries.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class TimeEntryResponse(BaseModel):
    """Schema for time entry response."""
    id: int
    employee_id: int
    type: Literal["IN", "OUT"]
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
