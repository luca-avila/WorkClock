"""
AdminUser model for system administrators.
Handles authentication and authorization for the admin dashboard.
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AdminUser(Base):
    """
    Admin user for dashboard access.

    Admins can:
    - Manage employees (create, edit, deactivate)
    - View shift reports
    - Calculate monthly payments
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AdminUser(id={self.id}, email='{self.email}')>"
