"""OpenMusic API application entrypoint.

Sets up the FastAPI app, registers the API router, and centralizes exception
handling to return consistent JSON responses to clients. Exception handlers map
framework and domain errors into a standardized response schema without leaking
internal details.
"""

from contextlib import asynccontextmanager
from typing import Dict
import aio_pika
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.api import api_router
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.error_codes import ErrorCode
from app.core.database import engine
from sqlalchemy import text
from app.services.cache_service import cache_service
from app.core.config import settings
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

logger = get_logger("openmusic")


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbit_connection = None
    try:
        logger.info("Starting up application", extra={"event": "startup"})
        rabbit_connection = await aio_pika.connect_robust(settings.RABBITMQ_SERVER)
        app.state.rabbit_connection = rabbit_connection
    except Exception as exc:
        logger.error("Failed to initialize RabbitMQ connection", exc_info=True)
        app.state.rabbit_connection = None

    try:
        yield
    finally:
        logger.info("Shutting down application", extra={"event": "shutdown"})
        try:
            await engine.dispose()
            logger.info("Closed database engine")
        except Exception:
            logger.error("Error closing database engine", exc_info=True)

        try:
            await cache_service.close()
            logger.info("Closed Redis cache client")
        except Exception:
            logger.error("Error closing Redis client", exc_info=True)

        try:
            if rabbit_connection:
                await rabbit_connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception:
            logger.error("Error closing RabbitMQ connection", exc_info=True)


app = FastAPI(title="OpenMusic API", lifespan=lifespan)

# Middleware registration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware, logger=logger)

# Register versioned API routes
app.include_router(api_router)


@app.get("/healthz")
async def healthcheck() -> Dict[str, str]:
    statuses: Dict[str, str] = {}
    http_status = status.HTTP_200_OK

    # DB check
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        statuses["db"] = "up"
    except Exception as exc:
        statuses["db"] = "down"
        logger.error("Healthcheck DB failure", exc_info=True)
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # Redis check
    try:
        pong = await cache_service.client.ping()
        statuses["redis"] = "up" if pong else "down"
        if not pong:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    except Exception:
        statuses["redis"] = "down"
        logger.error("Healthcheck Redis failure", exc_info=True)
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    # RabbitMQ check
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_SERVER)
        await connection.close()
        statuses["rabbitmq"] = "up"
    except Exception:
        statuses["rabbitmq"] = "down"
        logger.error("Healthcheck RabbitMQ failure", exc_info=True)
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=http_status, content=statuses)


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
        content={
            "status": "fail",
            "message": f"Validation Error: {error_msg}",
            "errorCode": ErrorCode.VALIDATION_ERROR,
        },
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
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.VALIDATION_ERROR,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Map domain AuthenticationError to a 401 response."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.AUTHENTICATION_FAILED,
        },
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Map authorization failure to 403 response."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.AUTHORIZATION_FAILED,
        },
    )


@app.exception_handler(ForbiddenError)
async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
    """Map domain ForbiddenError to a 403 response."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.AUTHORIZATION_FAILED,
        },
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.CONFLICT,
        },
    )


@app.exception_handler(PayloadTooLargeError)
async def payload_too_large_exception_handler(request: Request, exc: PayloadTooLargeError):
    """Map payload too large errors to a 413 response."""
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.VALIDATION_ERROR,
        },
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
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": getattr(exc, "error_code", None) or ErrorCode.RESOURCE_NOT_FOUND,
        },
    )


@app.exception_handler(PayloadTooLargeError)
async def payload_too_large_exception_handler(request: Request, exc: PayloadTooLargeError):
    """Map payload too large errors to a 413 response."""
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
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
    logger.error(
        "Global Exception",
        exc_info=True,
        extra={"path": str(request.url.path)},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal Server Error",
            "errorCode": ErrorCode.INTERNAL_ERROR,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "fail",
            "message": str(exc),
            "errorCode": ErrorCode.VALIDATION_ERROR,
        },
    )
