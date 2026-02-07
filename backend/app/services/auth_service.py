"""
Authentication service for admin user login and token management.
"""
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.schemas.auth import Token
from app.utils.security import verify_password, create_access_token
from app.config import settings


async def authenticate_admin(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[AdminUser]:
    """
    Authenticate an admin user by email and password.

    Args:
        db: Database session
        email: Admin email address
        password: Plain text password

    Returns:
        AdminUser if authentication successful, None otherwise

    Example:
        admin = await authenticate_admin(db, "admin@example.com", "password123")
        if admin:
            print(f"Authenticated: {admin.email}")
    """
    # Query admin by email
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == email)
    )
    admin = result.scalar_one_or_none()

    # Verify admin exists and password matches
    if not admin:
        return None

    if not verify_password(password, admin.hashed_password):
        return None

    return admin


async def login(db: AsyncSession, email: str, password: str) -> Token:
    """
    Authenticate admin and create access token.

    Args:
        db: Database session
        email: Admin email address
        password: Plain text password

    Returns:
        Token schema with access_token and token_type

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        token = await login(db, "admin@example.com", "password123")
        # Returns: Token(access_token="eyJ...", token_type="bearer")
    """
    # Authenticate admin
    admin = await authenticate_admin(db, email, password)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"email": admin.email},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
