"""OpenMusic API application entrypoint.

Sets up the FastAPI app, registers the API router, and centralizes exception
handling to return consistent JSON responses to clients. Exception handlers map
framework and domain errors into a standardized response schema without leaking
internal details.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.api import api_router
from app.core.exceptions import NotFoundError, ValidationError, AuthenticationError

app = FastAPI(title="OpenMusic API")

# Register versioned API routes
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors raised by FastAPI/Pydantic.

    Aggregates field-level validation messages into a concise, human-friendly
    sentence and returns a 400 response following the project's standard JSON
    envelope. This keeps client contracts stable and avoids exposing raw
    Pydantic error structures.

    Args:
        request: The incoming HTTP request.
        exc: The RequestValidationError raised during request parsing/validation.

    Returns:
        JSONResponse: A 400 response with a uniform payload, e.g.
        {"status": "fail", "message": "Validation Error: <details>"}.
    """
    # Simplified message for validation errors
    errors = exc.errors()
    error_msg = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in errors])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "fail", "message": f"Validation Error: {error_msg}"},
    )


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(request: Request, exc: ValidationError):
    """Map domain-level validation errors to a 400 response.

    This captures application-specific validation failures and returns a
    consistent error payload understood by clients.

    Args:
        request: The incoming HTTP request.
        exc: Domain ValidationError containing a human-readable message.

    Returns:
        JSONResponse: A 400 response with {"status": "fail", "message": str(exc)}.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"status": "fail", "message": str(exc)},
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Map domain AuthenticationError to a 401 response."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"status": "fail", "message": str(exc)},
    )


@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Map domain NotFoundError to a 404 response.

    Keeps resource-not-found semantics consistent across the API.

    Args:
        request: The incoming HTTP request.
        exc: NotFoundError raised by the domain/service layer.

    Returns:
        JSONResponse: A 404 response with {"status": "fail", "message": str(exc)}.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"status": "fail", "message": str(exc)},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler returning a generic 500 response.

    Prevents leaking internal error details to clients while providing a
    stable error envelope. In production, this should log to a structured
    logger/monitoring system instead of printing to stdout.

    Args:
        request: The incoming HTTP request.
        exc: The unhandled exception instance.

    Returns:
        JSONResponse: A 500 response with {"status": "error", "message": "Internal Server Error"}.
    """
    # Log the error here in a real app
    print(f"Global error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal Server Error"},
    )
