"""Standard response schemas for API responses."""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from app.core.error_codes import ErrorCode

T = TypeVar("T")


class ErrorResponse(BaseModel):
    status: str = Field(default="fail", example="fail")
    message: str = Field(..., example="Validation Error: title is required")
    errorCode: Optional[ErrorCode] = Field(default=None, example="VALIDATION_ERROR")


class StandardResponse(BaseModel, Generic[T]):
    status: str = Field(..., example="success")
    message: Optional[str] = Field(default=None, example="Operation completed")
    data: Optional[T] = None
