"""Advanced integration tests for Album and Song endpoints.

Covers nested data retrieval (album with songs) and search behavior including
case-insensitive filtering and combined (AND) criteria. Verifies response
structure remains consistent with simplified song projections.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_album_with_songs(client: AsyncClient):
    """Album detail includes simplified songs after creating linked songs."""
    # 1. Create Album
    album_payload = {"name": "Test Album", "year": 2023}
    res_album = await client.post("/albums/", json=album_payload)
    album_id = res_album.json()["data"]["albumId"]

    # 2. Create Songs linked to Album
    song1 = {
        "title": "Song 1",
        "year": 2023,
        "genre": "Rock",
        "performer": "Artist A",
        "albumId": album_id
    }
    song2 = {
        "title": "Song 2",
        "year": 2023,
        "genre": "Pop",
        "performer": "Artist B",
        "albumId": album_id
    }
    await client.post("/songs/", json=song1)
    await client.post("/songs/", json=song2)

    # 3. Get Album and Verify Songs List
    response = await client.get(f"/albums/{album_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    album = data["data"]["album"]
    assert "songs" in album
    assert len(album["songs"]) == 2
    
    # Verify strict structure (Simplified Song)
    first_song = album["songs"][0]
    assert "id" in first_song
    assert "title" in first_song
    assert "performer" in first_song
    assert "year" not in first_song  # Should be excluded
    assert "genre" not in first_song # Should be excluded

@pytest.mark.asyncio
async def test_song_search(client: AsyncClient):
    """Case-insensitive search by title/performer and AND-combined filters."""
    # Setup Data
    songs = [
        {"title": "Yellow", "year": 2000, "genre": "Rock", "performer": "Coldplay"},
        {"title": "Fix You", "year": 2005, "genre": "Rock", "performer": "Coldplay"},
        {"title": "Wonderwall", "year": 1995, "genre": "Rock", "performer": "Oasis"},
    ]
    for song in songs:
        await client.post("/songs/", json=song)

    # 1. Search by Performer
    res = await client.get("/songs/?performer=cold")
    data = res.json()["data"]["songs"]
    # Should find 2 Coldplay songs (Yellow, Fix You)
    # Note: Test database might not be reset between tests depending on fixture scope,
    # so we check if at least these 2 are present or count relative to this test run.
    # Assuming fresh DB or at least containing these:
    coldplay_songs = [s for s in data if s["performer"] == "Coldplay"]
    assert len(coldplay_songs) >= 2

    # 2. Search by Title
    res = await client.get("/songs/?title=wall")
    data = res.json()["data"]["songs"]
    wall_songs = [s for s in data if "Wonderwall" in s["title"]]
    assert len(wall_songs) >= 1

    # 3. Combined Search (AND logic)
    res = await client.get("/songs/?title=yellow&performer=oasis")
    data = res.json()["data"]["songs"]
    assert len(data) == 0 # Should match nothing
