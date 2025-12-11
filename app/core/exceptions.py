"""Domain-level exceptions for OpenMusic API.

Defines a small hierarchy of exceptions raised by the service layer.
These are translated to HTTP errors by FastAPI exception handlers.
"""

from typing import Optional
from app.core.error_codes import ErrorCode


class OpenMusicException(Exception):
    """Base class for domain-level errors in OpenMusic."""

    def __init__(self, message: str = "", error_code: Optional[ErrorCode] = None):
        super().__init__(message)
        self.error_code = error_code


class NotFoundError(OpenMusicException):
    """Raised when a requested entity does not exist."""
    pass


class ValidationError(OpenMusicException):
    """Raised when input violates business rules or constraints."""
    pass


class AuthenticationError(OpenMusicException):
    """Raised when authentication credentials are invalid."""
    pass


class ForbiddenError(OpenMusicException):
    """Raised when access is denied."""
    pass


class ConflictError(OpenMusicException):
    """Raised when a resource conflict occurs (e.g., duplicates)."""
    pass


class AuthorizationError(ForbiddenError):
    """Raised when token is valid but user lacks permissions."""
    pass


class PayloadTooLargeError(OpenMusicException):
    """Raised when a payload exceeds allowed limits."""
    pass

