"""Standard response schemas for API responses."""

from typing import Generic, Optional, TypeVar
from pydantic import BaseModel
from app.core.error_codes import ErrorCode

T = TypeVar("T")


class ErrorResponse(BaseModel):
    status: str = "fail"
    message: str
    errorCode: Optional[ErrorCode] = None


class StandardResponse(BaseModel, Generic[T]):
    status: str
    message: Optional[str] = None
    data: Optional[T] = None
