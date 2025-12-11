"""Pydantic schemas for Authentication operations.
"""

from pydantic import BaseModel, Field

class LoginPayload(BaseModel):
    """Schema for login request."""
    username: str = Field(..., example="music_fan_123")
    password: str = Field(..., example="Str0ngPass!")

class RefreshTokenPayload(BaseModel):
    """Schema for refresh token request."""
    refreshToken: str = Field(..., example="<refresh-jwt>")

class AuthToken(BaseModel):
    """Schema for returning auth tokens."""
    accessToken: str = Field(..., example="<access-jwt>")
    refreshToken: str = Field(..., example="<refresh-jwt>")
