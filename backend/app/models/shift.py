"""
Shift model - Derived state from TimeEntry pairs.

CRITICAL: Shifts are ONLY created by ClockService during clock-out actions.
They represent completed work periods with payment information.
"""
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Shift(Base):
    """
    Completed work shift derived from TimeEntry IN→OUT pairs.

    Invariant 5: Shifts are created only from valid IN→OUT pairs.

    A shift records:
    - When the employee started (clock_in)
    - When the employee finished (clock_out)
    - How much they earned (daily_rate at time of shift creation)

    IMPORTANT: money_gained stores the employee's daily_rate at shift creation time,
    not calculated from hours worked. This is a fixed daily rate payment model.
    """
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer,
        ForeignKey('employees.id', ondelete='RESTRICT'),
        nullable=False
    )
    clock_in_id = Column(
        Integer,
        ForeignKey('time_entries.id', ondelete='RESTRICT'),
        unique=True,
        nullable=False
    )
    clock_out_id = Column(
        Integer,
        ForeignKey('time_entries.id', ondelete='RESTRICT'),
        unique=True,
        nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=False)
    money_gained = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="shifts")
    clock_in = relationship("TimeEntry", foreign_keys=[clock_in_id])
    clock_out = relationship("TimeEntry", foreign_keys=[clock_out_id])

    # Constraints
    __table_args__ = (
        CheckConstraint('ended_at > started_at', name='check_shift_times'),
        CheckConstraint('money_gained >= 0', name='check_money_gained_positive'),
        # Composite index for reporting queries
        Index('idx_employee_started', 'employee_id', 'started_at'),
    )

    def __repr__(self):
        return f"<Shift(id={self.id}, employee_id={self.employee_id}, started={self.started_at}, ended={self.ended_at}, money=${self.money_gained})>"
