"""Unit tests for Export Playlist feature (Producer & Consumer).

Tests API endpoint (Producer) and Worker processing (Consumer) using mocks.
Does NOT connect to real RabbitMQ or SMTP.
"""

import json
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.api.deps import get_current_user
from app.main import app

# ============================================================================
# PART 1: PRODUCER API TESTS
# ============================================================================

@pytest.fixture
def mock_producer_service():
    """Mock ProducerService."""
    mock = MagicMock()
    mock.send_message = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_playlist_service():
    """Mock PlaylistService."""
    mock = MagicMock()
    mock.get_playlist_by_id = AsyncMock()
    return mock


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
async def test_client(transport):
    """Create test client."""
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_export_playlist_success(test_client, mock_producer_service, mock_playlist_service):
    """Test successful export request."""
    # Setup Override Auth
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    
    # Setup Mocks
    mock_playlist = MagicMock()
    mock_playlist.owner = "user-123"
    mock_playlist.id = "playlist-1"
    
    # Force return value using side_effect to be safer
    async def get_pl(*args, **kwargs):
        return mock_playlist
    mock_playlist_service.get_playlist_by_id.side_effect = get_pl
    
    with patch("app.api.v1.endpoints.exports.producer_service", mock_producer_service), \
         patch("app.api.v1.endpoints.exports.PlaylistService", return_value=mock_playlist_service):
        
        response = await test_client.post(
            "/export/playlists/playlist-1",
            json={"targetEmail": "test@example.com"}
        )
        # Assertions
        # Assertions
        assert response.status_code == 201, f"Failed with {response.status_code}. Response: {response.text}"
        assert response.json()["status"] == "success"
        
        # Verify Producer was called
        mock_producer_service.send_message.assert_called_once()
        args = mock_producer_service.send_message.call_args[0]
        assert args[0] == "export:playlist"
        assert args[1]["playlistId"] == "playlist-1"
        assert args[1]["targetEmail"] == "test@example.com"
        
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_playlist_forbidden(test_client, mock_producer_service, mock_playlist_service):
    """Test export request by non-owner returns 403."""
    app.dependency_overrides[get_current_user] = lambda: "user-999"  # Diff user
    
    # Setup Mocks
    mock_playlist = MagicMock()
    mock_playlist.owner = "user-123"
    
    async def get_pl(*args, **kwargs):
        return mock_playlist
    mock_playlist_service.get_playlist_by_id.side_effect = get_pl
    
    with patch("app.api.v1.endpoints.exports.producer_service", mock_producer_service), \
         patch("app.api.v1.endpoints.exports.PlaylistService", return_value=mock_playlist_service):
        
        response = await test_client.post(
            "/export/playlists/playlist-1",
            json={"targetEmail": "test@example.com"}
        )
        
        assert response.status_code == 403
        mock_producer_service.send_message.assert_not_called()
        
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_export_playlist_not_found(test_client, mock_producer_service, mock_playlist_service):
    """Test export request for non-existent playlist returns 404."""
    app.dependency_overrides[get_current_user] = lambda: "user-123"
    
    mock_playlist_service.get_playlist_by_id.return_value = None
    
    with patch("app.api.v1.endpoints.exports.producer_service", mock_producer_service), \
         patch("app.api.v1.endpoints.exports.PlaylistService", return_value=mock_playlist_service):
        
        response = await test_client.post(
            "/export/playlists/playlist-999",
            json={"targetEmail": "test@example.com"}
        )
        
        assert response.status_code == 404
        mock_producer_service.send_message.assert_not_called()
        
    app.dependency_overrides.clear()


# ============================================================================
# PART 2: CONSUMER WORKER TESTS
# ============================================================================

from app.consumer import Consumer

@pytest.fixture
def mock_mail_service():
    mock = MagicMock()
    mock.send_email = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_consumer_process_success(mock_mail_service):
    """Test consumer processes message correctly."""
    # Mock Data
    consumer = Consumer()
    consumer.get_playlist_data = AsyncMock(return_value={
        "playlist": {
            "id": "playlist-1",
            "name": "Test PL",
            "songs": [{"id": "s1", "title": "T1", "performer": "P1"}]
        }
    })
    
    # Create Mock Message
    mock_message = MagicMock()
    mock_message.body = json.dumps({
        "playlistId": "playlist-1", 
        "targetEmail": "user@test.com"
    }).encode()
    mock_message.process = MagicMock()
    # Mock context manager for message.process
    mock_message.process.return_value.__aenter__.return_value = None
    mock_message.process.return_value.__aexit__.return_value = None
    
    with patch("app.consumer.mail_service", mock_mail_service):
        await consumer.process_message(mock_message)
        
        # Assertions
        consumer.get_playlist_data.assert_called_once_with("playlist-1")
        mock_mail_service.send_email.assert_called_once()
        
        # Verify Email Content
        call_args = mock_mail_service.send_email.call_args[1]
        assert call_args["target_email"] == "user@test.com"
        assert "Test PL" in call_args["subject"]
        assert "s1" in call_args["content"]
