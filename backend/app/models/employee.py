"""
Employee model for workforce management.
Each employee has a unique 4-digit clock code for kiosk access.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    """
    Employee record with clock code for kiosk access.

    Invariant 1: Clock code must be unique among active employees.
    A deactivated employee's code can be reused by a new employee.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    job_role = Column(String(255), nullable=False)
    daily_rate = Column(Numeric(10, 2), nullable=False)
    clock_code = Column(String(4), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    time_entries = relationship("TimeEntry", back_populates="employee")
    shifts = relationship("Shift", back_populates="employee")

    # Constraints
    __table_args__ = (
        CheckConstraint('daily_rate >= 0', name='check_daily_rate_positive'),
        CheckConstraint("clock_code ~ '^[0-9]{4}$'", name='check_clock_code_format'),
        # Unique constraint only for active employees (allows code reuse after deactivation)
        Index('idx_active_clock_code', 'clock_code', unique=True, postgresql_where=(is_active == True)),
        Index('idx_employee_created', 'created_at'),
    )

    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', code='{self.clock_code}', active={self.is_active})>"
