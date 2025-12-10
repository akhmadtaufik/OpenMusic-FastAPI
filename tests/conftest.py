"""Test configuration and fixtures for OpenMusic API.

Provides async DB session, HTTP client, authentication helpers, and mocks
for external services (Storage, Redis, RabbitMQ).
"""

import pytest
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base
from app.core.config import settings
from app.main import app
from app.api.deps import get_db


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated async SQLAlchemy session for each test.
    
    Creates a new engine per test to avoid connection conflicts.
    Tables are created before and dropped after each test.
    """
    # Create engine per test to avoid connection sharing issues
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI, 
        echo=False,
        pool_pre_ping=True
    )
    
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Yield session
    async with SessionLocal() as session:
        yield session
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTPX AsyncClient wired to the FastAPI app."""
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Create and return a registered user with credentials."""
    payload = {
        "username": "testuser",
        "password": "testpass123",
        "fullname": "Test User"
    }
    response = await client.post("/users/", json=payload)
    user_id = response.json()["data"]["userId"]
    return {
        "userId": user_id,
        "username": payload["username"],
        "password": payload["password"]
    }


@pytest.fixture
async def auth_token(client: AsyncClient, registered_user: dict) -> str:
    """Login and return access token for authenticated requests."""
    response = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    return response.json()["data"]["accessToken"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict:
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def second_user(client: AsyncClient) -> dict:
    """Create a second user for multi-user tests."""
    payload = {
        "username": "seconduser",
        "password": "secondpass123",
        "fullname": "Second User"
    }
    response = await client.post("/users/", json=payload)
    user_id = response.json()["data"]["userId"]
    return {
        "userId": user_id,
        "username": payload["username"],
        "password": payload["password"]
    }


@pytest.fixture
async def second_auth_headers(client: AsyncClient, second_user: dict) -> dict:
    """Return auth headers for the second user."""
    response = await client.post("/authentications/", json={
        "username": second_user["username"],
        "password": second_user["password"]
    })
    token = response.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# MOCKS FOR EXTERNAL SERVICES
# ============================================================================

@pytest.fixture
def mock_storage_service():
    """Mock StorageService to avoid real MinIO uploads."""
    with patch("app.services.storage_service.storage_service") as mock:
        mock.upload_file = AsyncMock(return_value="http://minio:9000/test/fake_cover.png")
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis/CacheService for cache hit/miss simulation."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    yield mock


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ producer to verify message sending."""
    with patch("app.services.producer_service.producer_service") as mock:
        mock.send_message = AsyncMock(return_value=True)
        yield mock


# ============================================================================
# HELPER DATA FIXTURES
# ============================================================================

@pytest.fixture
async def sample_album(client: AsyncClient) -> dict:
    """Create and return a sample album."""
    payload = {"name": "Test Album", "year": 2024}
    response = await client.post("/albums/", json=payload)
    album_id = response.json()["data"]["albumId"]
    return {"id": album_id, **payload}


@pytest.fixture
async def sample_song(client: AsyncClient, sample_album: dict) -> dict:
    """Create and return a sample song linked to an album."""
    payload = {
        "title": "Test Song",
        "year": 2024,
        "genre": "Rock",
        "performer": "Test Artist",
        "duration": 180,
        "albumId": sample_album["id"]
    }
    response = await client.post("/songs/", json=payload)
    song_id = response.json()["data"]["songId"]
    return {"id": song_id, **payload}


@pytest.fixture
async def sample_playlist(client: AsyncClient, auth_headers: dict) -> dict:
    """Create and return a sample playlist."""
    payload = {"name": "Test Playlist"}
    response = await client.post("/playlists/", json=payload, headers=auth_headers)
    playlist_id = response.json()["data"]["playlistId"]
    return {"id": playlist_id, **payload}
