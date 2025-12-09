"""Domain-level exceptions for OpenMusic API.

Defines a small hierarchy of exceptions raised by the service layer.
These are translated to HTTP errors by FastAPI exception handlers.
"""

class OpenMusicException(Exception):
    """Base class for domain-level errors in OpenMusic.

    Serves as a common ancestor to allow broad catching of business rule
    violations separately from system/runtime errors.
    """
    pass

class NotFoundError(OpenMusicException):
    """Raised when a requested entity does not exist.

    Typically mapped to an HTTP 404 by the API layer.
    """
    pass

class ValidationError(OpenMusicException):
    """Raised when input violates business rules or constraints.

    Typically mapped to an HTTP 400 by the API layer.
    """
    pass
