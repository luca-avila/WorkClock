"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Admin login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded in JWT token."""
    email: str | None = None
