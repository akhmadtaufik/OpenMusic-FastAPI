"""Unit tests for album likes caching logic.

Tests cache hit/miss scenarios and cache invalidation using mocks.
Does NOT connect to real Redis.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_cache_service():
    """Mock CacheService for testing cache behavior."""
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)  # Default: cache miss
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_like_service():
    """Mock LikeService for testing without DB."""
    mock = MagicMock()
    mock.get_likes_count = AsyncMock(return_value=10)
    mock.add_like = AsyncMock(return_value=None)
    mock.remove_like = AsyncMock(return_value=None)
    return mock


@pytest.fixture
async def test_client():
    """Create test client without DB dependency."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# CACHE MISS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_likes_cache_miss(test_client, mock_cache_service, mock_like_service):
    """Test GET /albums/{id}/likes on cache miss.
    
    When cache returns None:
    - DB service should be called
    - Cache should be populated
    - Response should contain correct count
    - X-Data-Source header should NOT be 'cache'
    """
    with patch("app.api.v1.endpoints.album_likes.cache_service", mock_cache_service), \
         patch("app.api.v1.endpoints.album_likes.LikeService") as MockLikeService:
        
        # Setup mock
        mock_cache_service.get.return_value = None  # Cache miss
        mock_instance = MockLikeService.return_value
        mock_instance.get_likes_count = AsyncMock(return_value=10)
        
        response = await test_client.get("/albums/album-test123/likes")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["likes"] == 10
        
        # Verify cache was checked
        mock_cache_service.get.assert_called_once_with("likes:album-test123")
        
        # Verify DB was called (cache miss)
        mock_instance.get_likes_count.assert_called_once_with("album-test123")
        
        # Verify cache was set
        mock_cache_service.set.assert_called_once_with(
            "likes:album-test123", "10", 1800
        )
        
        # Verify header is NOT 'cache'
        assert response.headers.get("X-Data-Source") != "cache"


# ============================================================================
# CACHE HIT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_likes_cache_hit(test_client, mock_cache_service, mock_like_service):
    """Test GET /albums/{id}/likes on cache hit.
    
    When cache returns a value:
    - DB service should NOT be called
    - Response should contain cached count
    - X-Data-Source header should be 'cache'
    """
    with patch("app.api.v1.endpoints.album_likes.cache_service", mock_cache_service), \
         patch("app.api.v1.endpoints.album_likes.LikeService") as MockLikeService:
        
        # Setup mock - cache hit returns "50"
        mock_cache_service.get.return_value = "50"
        mock_instance = MockLikeService.return_value
        mock_instance.get_likes_count = AsyncMock(return_value=999)
        
        response = await test_client.get("/albums/album-test456/likes")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["likes"] == 50  # From cache, not DB
        
        # Verify cache was checked
        mock_cache_service.get.assert_called_once_with("likes:album-test456")
        
        # Verify DB was NOT called (cache hit)
        mock_instance.get_likes_count.assert_not_called()
        
        # Verify cache was NOT set again
        mock_cache_service.set.assert_not_called()
        
        # Verify header is 'cache'
        assert response.headers.get("X-Data-Source") == "cache"


# ============================================================================
# CACHE INVALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_like_album_invalidates_cache(test_client, mock_cache_service):
    """Test POST /albums/{id}/likes invalidates cache."""
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    
    try:
        with patch("app.api.v1.endpoints.album_likes.cache_service", mock_cache_service), \
             patch("app.api.v1.endpoints.album_likes.LikeService") as MockLikeService:
            
            mock_instance = MockLikeService.return_value
            mock_instance.add_like = AsyncMock(return_value=None)
            
            response = await test_client.post(
                "/albums/album-test789/likes",
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 201
            
            # Verify cache was deleted
            mock_cache_service.delete.assert_called_once_with("likes:album-test789")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unlike_album_invalidates_cache(test_client, mock_cache_service):
    """Test DELETE /albums/{id}/likes invalidates cache."""
    from app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    
    try:
        with patch("app.api.v1.endpoints.album_likes.cache_service", mock_cache_service), \
             patch("app.api.v1.endpoints.album_likes.LikeService") as MockLikeService:
            
            mock_instance = MockLikeService.return_value
            mock_instance.remove_like = AsyncMock(return_value=None)
            
            response = await test_client.delete(
                "/albums/album-test789/likes",
                headers={"Authorization": "Bearer fake-token"}
            )
            
            assert response.status_code == 200
            
            # Verify cache was deleted
            mock_cache_service.delete.assert_called_once_with("likes:album-test789")
    finally:
        app.dependency_overrides.clear()
