"""
API routers for the application.
"""
from app.routers.auth import router as auth_router
from app.routers.employees import router as employees_router
from app.routers.kiosk import router as kiosk_router

__all__ = ["auth_router", "employees_router", "kiosk_router"]
