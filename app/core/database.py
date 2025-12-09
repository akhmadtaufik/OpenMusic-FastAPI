"""Database setup for OpenMusic API.

Initializes the global async SQLAlchemy engine, exposes an async session
factory for per-request database access, and defines the declarative base
for ORM models.
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Global async SQLAlchemy engine; created once for the application lifetime.
# echo=False avoids verbose SQL logging by default.
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)

# Async session factory used by request-scoped dependencies.
# - expire_on_commit=False keeps loaded attributes usable after commit
# - autoflush=False gives explicit control over when SQL is flushed
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    All SQLAlchemy models in this project should inherit from this base to
    share the same metadata and mapper configuration.
    """
    pass
