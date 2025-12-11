"""V3 Features tests for OpenMusic API.

Covers album cover upload and album likes functionality.
"""

import pytest
from io import BytesIO
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


# ============================================================================
# ALBUM COVER UPLOAD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_upload_cover_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_album: dict
):
    """Upload valid cover image returns 201."""
    # Create a small valid image (PNG header)
    image_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    
    with patch("app.api.v1.endpoints.albums.storage_service") as mock_storage:
        mock_storage.upload_file = AsyncMock(
            return_value="http://minio:9000/openmusic/test_cover.png"
        )
        
        response = await client.post(
            f"/albums/{sample_album['id']}/covers",
            files={"cover": ("test.png", BytesIO(image_content), "image/png")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "Sampul berhasil diunggah" in data["message"]


@pytest.mark.asyncio
async def test_upload_cover_invalid_type(
    client: AsyncClient,
    sample_album: dict
):
    """Upload non-image file returns 400."""
    text_content = b"This is not an image"
    
    response = await client.post(
        f"/albums/{sample_album['id']}/covers",
        files={"cover": ("test.txt", BytesIO(text_content), "text/plain")}
    )
    
    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_cover_too_large(
    client: AsyncClient,
    sample_album: dict
):
    """Upload file > 512KB returns 400."""
    # Create content larger than 512KB
    large_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * (512_001)
    
    response = await client.post(
        f"/albums/{sample_album['id']}/covers",
        files={"cover": ("large.png", BytesIO(large_content), "image/png")}
    )
    
    assert response.status_code == 400
    assert "512" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cover_url_persisted(
    client: AsyncClient,
    sample_album: dict
):
    """After upload, album GET returns coverUrl."""
    image_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    fake_url = "http://minio:9000/openmusic/test_cover.png"
    
    with patch("app.api.v1.endpoints.albums.storage_service") as mock_storage:
        mock_storage.upload_file = AsyncMock(return_value=fake_url)
        
        await client.post(
            f"/albums/{sample_album['id']}/covers",
            files={"cover": ("test.png", BytesIO(image_content), "image/png")}
        )
    
    # Verify coverUrl is set
    response = await client.get(f"/albums/{sample_album['id']}")
    album = response.json()["data"]["album"]
    assert album["coverUrl"] == fake_url


# ============================================================================
# ALBUM LIKES TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_like_album_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_album: dict
):
    """Like album returns 201."""
    response = await client.post(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "Menyukai album" in data["message"]


@pytest.mark.asyncio
async def test_like_album_double_like(
    client: AsyncClient,
    auth_headers: dict,
    sample_album: dict
):
    """Double like returns 400."""
    # First like
    await client.post(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    # Second like - should fail
    response = await client.post(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "fail"
    assert "already liked" in data["message"].lower()


@pytest.mark.asyncio
async def test_unlike_album_success(
    client: AsyncClient,
    auth_headers: dict,
    sample_album: dict
):
    """Unlike album returns 200."""
    # First like
    await client.post(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    # Unlike
    response = await client.delete(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Batal menyukai album" in data["message"]


@pytest.mark.asyncio
async def test_get_likes_count(
    client: AsyncClient,
    auth_headers: dict,
    sample_album: dict
):
    """Get likes count returns correct number."""
    # Initial count should be 0
    response = await client.get(f"/albums/{sample_album['id']}/likes")
    assert response.json()["data"]["likes"] == 0
    
    # Like the album
    await client.post(
        f"/albums/{sample_album['id']}/likes",
        headers=auth_headers
    )
    
    # Count should be 1
    response = await client.get(f"/albums/{sample_album['id']}/likes")
    assert response.json()["data"]["likes"] == 1


@pytest.mark.asyncio
async def test_get_likes_public(client: AsyncClient, sample_album: dict):
    """Get likes count works without authentication."""
    response = await client.get(f"/albums/{sample_album['id']}/likes")
    
    assert response.status_code == 200
    assert "likes" in response.json()["data"]


@pytest.mark.asyncio
async def test_like_album_nonexistent(
    client: AsyncClient,
    auth_headers: dict
):
    """Like non-existent album returns 404."""
    response = await client.post(
        "/albums/album-nonexistent/likes",
        headers=auth_headers
    )
    
    assert response.status_code == 404
