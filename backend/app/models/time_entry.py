"""
TimeEntry model - Immutable audit log of all clock events.

CRITICAL: This is an append-only table. Time entries are NEVER updated or deleted.
All clock-in and clock-out actions create new entries, maintaining a complete history.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TimeEntry(Base):
    """
    Immutable time entry for clock-in/out events.

    Invariant 4: Time entries are append-only and never modified.
    This provides a complete audit trail of all clock actions.

    Each entry is either:
    - 'IN': Employee clocked in (shift started)
    - 'OUT': Employee clocked out (shift ended)
    """
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey('employees.id', ondelete='RESTRICT'),
        nullable=False
    )
    type = Column(String(3), nullable=False)  # 'IN' or 'OUT'
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="time_entries")

    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('IN', 'OUT')", name='check_time_entry_type'),
        # Composite index for fast lookups of employee's time entries
        Index('idx_employee_timestamp', 'employee_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, employee_id={self.employee_id}, type='{self.type}', timestamp={self.timestamp})>"
