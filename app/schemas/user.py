"""Pydantic schemas for User operations.
"""
import re
from pydantic import BaseModel, ConfigDict, field_validator

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    username: str
    password: str
    fullname: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{4,50}", v):
            raise ValueError("Username must be 4-50 chars and alphanumeric/underscore")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("fullname")
    @classmethod
    def clean_fullname(cls, v: str) -> str:
        return v.strip()

class UserResponse(BaseModel):
    """Schema for returning user details (no password)."""
    id: str
    username: str
    fullname: str

    model_config = ConfigDict(from_attributes=True)
