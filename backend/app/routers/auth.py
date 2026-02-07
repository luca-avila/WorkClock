"""
Authentication router for admin login.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, Token
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login_endpoint(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Admin login endpoint.

    Authenticates an admin user with email and password, returns a JWT access token.

    Args:
        credentials: LoginRequest with email and password
        db: Database session (injected)

    Returns:
        Token with access_token and token_type

    Raises:
        HTTPException: 401 if authentication fails

    Example Request:
        POST /auth/login
        {
            "email": "admin@example.com",
            "password": "SecurePassword123"
        }

    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }

    Usage:
        1. Admin enters email/password in login form
        2. Frontend sends POST request to this endpoint
        3. If valid, receive JWT token
        4. Store token in localStorage
        5. Send token in Authorization header for subsequent requests
    """
    return await login(db, credentials.email, credentials.password)
