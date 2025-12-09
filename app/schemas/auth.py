"""Pydantic schemas for Authentication operations.
"""

from pydantic import BaseModel

class LoginPayload(BaseModel):
    """Schema for login request."""
    username: str
    password: str

class RefreshTokenPayload(BaseModel):
    """Schema for refresh token request."""
    refreshToken: str

class AuthToken(BaseModel):
    """Schema for returning auth tokens."""
    accessToken: str
    refreshToken: str
