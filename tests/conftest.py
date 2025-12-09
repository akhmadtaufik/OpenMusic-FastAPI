"""Test configuration and fixtures for OpenMusic API.

Provides async DB session and HTTP client fixtures. The DB fixture sets up a
fresh schema per test to ensure isolation and deterministic results.
"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.main import app
from app.api.deps import get_db

@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async SQLAlchemy session for each test.

    Creates a dedicated engine and session factory per-test to avoid event
    loop conflicts and ensure clean teardown. The schema is created before
    yielding the session and dropped afterwards.

    Yields:
        AsyncSession: The active database session for the test.
    """
    # Create engine per test to avoid loop issues
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False)
    TestingSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    
    # Create tables for the test schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    # Drop all tables to reset state between tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()

@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTPX AsyncClient wired to the FastAPI app.

    Overrides the app's database dependency to use the per-test async session.
    Uses in-memory ASGITransport to avoid real network I/O.

    Yields:
        AsyncClient: Configured client for calling API endpoints.
    """
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Restore original dependencies after use
    app.dependency_overrides.clear()
