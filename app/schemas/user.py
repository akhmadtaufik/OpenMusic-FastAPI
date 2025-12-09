"""Pydantic schemas for User operations.
"""

from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    password: str
    fullname: str

class UserResponse(BaseModel):
    """Schema for returning user details (no password)."""
    id: str
    username: str
    fullname: str

    model_config = ConfigDict(from_attributes=True)
