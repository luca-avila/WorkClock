"""
FastAPI dependencies for authentication and database sessions.
"""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.auth import TokenData
from app.utils.security import decode_access_token

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> AdminUser:
    """
    Dependency to get the current authenticated admin from JWT token.

    This dependency:
    1. Extracts JWT token from Authorization header
    2. Decodes and validates the token
    3. Queries the admin user from database
    4. Returns the admin user or raises 401 error

    Args:
        token: JWT token from Authorization header (automatically extracted)
        db: Database session (automatically injected)

    Returns:
        Authenticated AdminUser instance

    Raises:
        HTTPException: 401 if token is invalid or admin not found

    Usage:
        @router.get("/protected")
        async def protected_route(admin: AdminUser = Depends(get_current_admin)):
            return {"message": f"Hello {admin.email}"}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = decode_access_token(token)

        if payload is None:
            raise credentials_exception

        # Extract email from token
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email)

    except JWTError:
        raise credentials_exception

    # Query admin from database
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == token_data.email)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        raise credentials_exception

    return admin
