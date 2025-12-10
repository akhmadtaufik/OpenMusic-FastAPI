"""Albums & Songs tests for OpenMusic API.

Covers CRUD operations, validation, and response structure verification.
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# ALBUM TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_album_success(client: AsyncClient):
    """Create album returns 201 with albumId."""
    payload = {"name": "New Album", "year": 2024}
    response = await client.post("/albums/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "albumId" in data["data"]


@pytest.mark.asyncio
async def test_create_album_missing_name(client: AsyncClient):
    """Missing required field returns 400."""
    payload = {"year": 2024}  # Missing name
    response = await client.post("/albums/", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "fail"


@pytest.mark.asyncio
async def test_get_album_with_cover_url(client: AsyncClient, sample_album: dict):
    """Album detail includes coverUrl field."""
    response = await client.get(f"/albums/{sample_album['id']}")
    
    assert response.status_code == 200
    album = response.json()["data"]["album"]
    assert "coverUrl" in album  # Should be present (even if None)
    assert "songs" in album  # Songs list should be present


@pytest.mark.asyncio
async def test_get_album_not_found(client: AsyncClient):
    """Non-existent album returns 404."""
    response = await client.get("/albums/album-nonexistent")
    
    assert response.status_code == 404
    assert response.json()["status"] == "fail"


@pytest.mark.asyncio
async def test_update_album(client: AsyncClient, sample_album: dict):
    """Update album modifies fields correctly."""
    payload = {"name": "Updated Album", "year": 2025}
    response = await client.put(f"/albums/{sample_album['id']}", json=payload)
    
    assert response.status_code == 200
    
    # Verify update
    get_res = await client.get(f"/albums/{sample_album['id']}")
    album = get_res.json()["data"]["album"]
    assert album["name"] == "Updated Album"
    assert album["year"] == 2025


@pytest.mark.asyncio
async def test_delete_album(client: AsyncClient, sample_album: dict):
    """Delete album removes it from database."""
    response = await client.delete(f"/albums/{sample_album['id']}")
    assert response.status_code == 200
    
    # Verify deletion
    get_res = await client.get(f"/albums/{sample_album['id']}")
    assert get_res.status_code == 404


# ============================================================================
# SONG TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_song_success(client: AsyncClient):
    """Create song returns 201 with songId."""
    payload = {
        "title": "New Song",
        "year": 2024,
        "genre": "Rock",
        "performer": "Artist"
    }
    response = await client.post("/songs/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "songId" in data["data"]


@pytest.mark.asyncio
async def test_create_song_missing_title(client: AsyncClient):
    """Missing required field returns 400."""
    payload = {"year": 2024, "genre": "Rock", "performer": "Artist"}
    response = await client.post("/songs/", json=payload)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_song_list_simplified(client: AsyncClient, sample_song: dict):
    """Song list contains only simplified fields."""
    response = await client.get("/songs/")
    
    assert response.status_code == 200
    songs = response.json()["data"]["songs"]
    assert len(songs) > 0
    
    song = songs[0]
    assert "id" in song
    assert "title" in song
    assert "performer" in song
    # These should NOT be in list view
    assert "year" not in song
    assert "genre" not in song


@pytest.mark.asyncio
async def test_song_detail_full(client: AsyncClient, sample_song: dict):
    """Song detail contains all fields."""
    response = await client.get(f"/songs/{sample_song['id']}")
    
    assert response.status_code == 200
    song = response.json()["data"]["song"]
    assert song["id"] == sample_song["id"]
    assert song["title"] == sample_song["title"]
    assert song["year"] == sample_song["year"]
    assert song["genre"] == sample_song["genre"]
    assert song["performer"] == sample_song["performer"]


@pytest.mark.asyncio
async def test_song_album_association(client: AsyncClient, sample_song: dict):
    """Song correctly links to album."""
    response = await client.get(f"/songs/{sample_song['id']}")
    song = response.json()["data"]["song"]
    assert song["albumId"] == sample_song["albumId"]


@pytest.mark.asyncio
async def test_album_contains_songs(client: AsyncClient, sample_song: dict, sample_album: dict):
    """Album detail includes its songs."""
    response = await client.get(f"/albums/{sample_album['id']}")
    album = response.json()["data"]["album"]
    
    assert "songs" in album
    assert len(album["songs"]) == 1
    assert album["songs"][0]["id"] == sample_song["id"]
