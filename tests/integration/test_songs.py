"""Integration tests for Song endpoints.

Validate full CRUD flows, list projections, validation errors, and album
associations. Assertions focus on HTTP status codes and standardized
response shapes.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_songs_happy_path(client: AsyncClient):
    """End-to-end CRUD flow for songs with shape checks on list/detail responses."""
    # 1. Create a Song
    payload = {
        "title": "Test Song",
        "year": 2023,
        "genre": "Rock",
        "performer": "Test Artist",
        "duration": 180
    }
    response = await client.post("/songs/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "songId" in data["data"]
    song_id = data["data"]["songId"]

    # 2. Get Song List (Verify shape)
    response = await client.get("/songs/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    songs = data["data"]["songs"]
    assert len(songs) > 0
    # Check fields of the first song (simplified view)
    first_song = songs[0]
    assert "id" in first_song
    assert "title" in first_song
    assert "performer" in first_song
    # Should NOT have other fields
    assert "year" not in first_song
    assert "genre" not in first_song

    # 3. Get Song Detail (Verify full fields)
    response = await client.get(f"/songs/{song_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    song = data["data"]["song"]
    assert song["id"] == song_id
    assert song["title"] == payload["title"]
    assert song["year"] == payload["year"]
    assert song["genre"] == payload["genre"]
    assert song["performer"] == payload["performer"]
    assert song["duration"] == payload["duration"]

    # 4. Update Song
    update_payload = {
        "title": "Updated Song",
        "year": 2024,
        "genre": "Pop",
        "performer": "Updated Artist",
        "duration": 200
    }
    response = await client.put(f"/songs/{song_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Song updated"

    # Verify Update
    response = await client.get(f"/songs/{song_id}")
    song = response.json()["data"]["song"]
    assert song["title"] == "Updated Song"

    # 5. Delete Song
    response = await client.delete(f"/songs/{song_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Song deleted"

    # Verify Deletion
    response = await client.get(f"/songs/{song_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_song_validation(client: AsyncClient):
    """Missing required fields produce a 400 validation error response."""
    payload = {
        "year": 2023,
        "genre": "Rock",
        "performer": "Artist"
        # Missing title
    }
    response = await client.post("/songs/", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "fail"

@pytest.mark.asyncio
async def test_song_album_association(client: AsyncClient):
    """Creating a song with albumId links it to the album and is reflected in detail."""
    # 1. Create Album
    album_payload = {"name": "Test Album", "year": 2023}
    res_album = await client.post("/albums/", json=album_payload)
    album_id = res_album.json()["data"]["albumId"]

    # 2. Create Song with Album ID
    song_payload = {
        "title": "Album Song",
        "year": 2023,
        "genre": "Rock",
        "performer": "Artist",
        "albumId": album_id
    }
    res_song = await client.post("/songs/", json=song_payload)
    song_id = res_song.json()["data"]["songId"]

    # 3. Verify Association
    res_get = await client.get(f"/songs/{song_id}")
    song = res_get.json()["data"]["song"]
    assert song["albumId"] == album_id
