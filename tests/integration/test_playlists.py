"""Playlist and ACL tests for OpenMusic API.

Covers playlist CRUD and access control (owner vs non-owner permissions).
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# PLAYLIST CRUD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_playlist_success(client: AsyncClient, auth_headers: dict):
    """Create playlist returns 201 with playlistId."""
    payload = {"name": "My Playlist"}
    response = await client.post("/playlists/", json=payload, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "playlistId" in data["data"]


@pytest.mark.asyncio
async def test_create_playlist_unauthorized(client: AsyncClient):
    """Create playlist without auth returns 401."""
    payload = {"name": "My Playlist"}
    response = await client.post("/playlists/", json=payload)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_playlists_owner_only(
    client: AsyncClient, 
    auth_headers: dict,
    second_auth_headers: dict
):
    """User only sees their own playlists."""
    # First user creates a playlist
    await client.post("/playlists/", json={"name": "User1 Playlist"}, headers=auth_headers)
    
    # Second user creates a playlist
    await client.post("/playlists/", json={"name": "User2 Playlist"}, headers=second_auth_headers)
    
    # First user gets playlists - should only see their own
    response = await client.get("/playlists/", headers=auth_headers)
    playlists = response.json()["data"]["playlists"]
    
    playlist_names = [p["name"] for p in playlists]
    assert "User1 Playlist" in playlist_names
    assert "User2 Playlist" not in playlist_names


# ============================================================================
# PLAYLIST SONGS AND ACL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_add_song_to_playlist_owner(
    client: AsyncClient,
    auth_headers: dict,
    sample_playlist: dict,
    sample_song: dict
):
    """Owner can add song to their playlist."""
    payload = {"songId": sample_song["id"]}
    response = await client.post(
        f"/playlists/{sample_playlist['id']}/songs",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_song_to_playlist_non_owner(
    client: AsyncClient,
    sample_playlist: dict,
    sample_song: dict,
    second_auth_headers: dict
):
    """Non-owner cannot add song to playlist (returns 403)."""
    payload = {"songId": sample_song["id"]}
    response = await client.post(
        f"/playlists/{sample_playlist['id']}/songs",
        json=payload,
        headers=second_auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_playlist_owner(
    client: AsyncClient,
    auth_headers: dict,
    sample_playlist: dict
):
    """Owner can delete their playlist."""
    response = await client.delete(
        f"/playlists/{sample_playlist['id']}",
        headers=auth_headers
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_playlist_non_owner(
    client: AsyncClient,
    sample_playlist: dict,
    second_auth_headers: dict
):
    """Non-owner cannot delete playlist (returns 403)."""
    response = await client.delete(
        f"/playlists/{sample_playlist['id']}",
        headers=second_auth_headers
    )
    
    assert response.status_code == 403
