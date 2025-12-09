"""Common FastAPI dependencies for the API layer.

Currently exposes an async database session provider used by route handlers.
Sessions are opened and closed per-request using the project-wide session
factory.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session.

    This function is intended for FastAPI dependency injection. It opens an
    async session from the global factory and ensures proper cleanup once the
    request is finished.

    Yields:
        AsyncSession: The active database session for the request.
    """
    async with AsyncSessionLocal() as session:
        yield session
