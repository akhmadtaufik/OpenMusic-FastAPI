"""Security tests for OpenMusic API.

Tests for authentication, authorization, rate limiting, token management,
and CORS security measures.
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# AUTHENTICATION TESTS (Vuln #1)
# ============================================================================

@pytest.mark.asyncio
async def test_delete_song_without_auth_returns_401(client: AsyncClient, auth_headers: dict):
    """DELETE /songs/{id} without auth token returns 401."""
    # First create a song with auth
    payload = {
        "title": "Test Song",
        "year": 2024,
        "genre": "Rock",
        "performer": "Test Artist",
        "duration": 180
    }
    response = await client.post("/songs/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    song_id = response.json()["data"]["songId"]
    
    # Try to delete without auth
    response = await client.delete(f"/songs/{song_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_song_without_auth_returns_401(client: AsyncClient, auth_headers: dict):
    """PUT /songs/{id} without auth token returns 401."""
    # First create a song with auth
    payload = {
        "title": "Test Song",
        "year": 2024,
        "genre": "Rock",
        "performer": "Test Artist",
        "duration": 180
    }
    response = await client.post("/songs/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    song_id = response.json()["data"]["songId"]
    
    # Try to update without auth
    update_payload = {"title": "Hacked Title", "year": 2024, "genre": "Pop", "performer": "Hacker", "duration": 100}
    response = await client.put(f"/songs/{song_id}", json=update_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_album_without_auth_returns_401(client: AsyncClient, auth_headers: dict):
    """DELETE /albums/{id} without auth token returns 401."""
    # First create an album with auth
    payload = {"name": "Test Album", "year": 2024}
    response = await client.post("/albums/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    album_id = response.json()["data"]["albumId"]
    
    # Try to delete without auth
    response = await client.delete(f"/albums/{album_id}")
    assert response.status_code == 401


# ============================================================================
# AUTHORIZATION TESTS (Vuln #3)
# ============================================================================

@pytest.mark.asyncio
async def test_delete_playlist_by_non_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict
):
    """Non-owner cannot delete another user's playlist."""
    # User A creates a playlist
    response = await client.post(
        "/playlists/",
        json={"name": "User A Playlist"},
        headers=auth_headers
    )
    assert response.status_code == 201
    playlist_id = response.json()["data"]["playlistId"]
    
    # User B tries to delete User A's playlist
    response = await client.delete(
        f"/playlists/{playlist_id}",
        headers=second_auth_headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_add_song_to_playlist_by_non_owner_returns_403(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    sample_song: dict
):
    """Non-owner/non-collaborator cannot add songs to playlist."""
    # User A creates a playlist
    response = await client.post(
        "/playlists/",
        json={"name": "Private Playlist"},
        headers=auth_headers
    )
    assert response.status_code == 201
    playlist_id = response.json()["data"]["playlistId"]
    
    # User B tries to add a song
    response = await client.post(
        f"/playlists/{playlist_id}/songs",
        json={"songId": sample_song["id"]},
        headers=second_auth_headers
    )
    assert response.status_code == 403


# ============================================================================
# TOKEN ROTATION TESTS (Vuln #4)
# ============================================================================

@pytest.mark.asyncio
async def test_old_refresh_token_invalid_after_rotation(client: AsyncClient, registered_user: dict):
    """After token refresh, the old refresh token should be invalid."""
    # Login to get initial tokens
    login_res = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    old_refresh_token = login_res.json()["data"]["refreshToken"]
    
    # Refresh tokens (this should invalidate old refresh token)
    refresh_res = await client.put("/authentications/", json={
        "refreshToken": old_refresh_token
    })
    assert refresh_res.status_code == 200
    
    # Try to use the old refresh token again - should fail
    reuse_res = await client.put("/authentications/", json={
        "refreshToken": old_refresh_token
    })
    # Should be 400 (token not found in DB) or 401 (invalid token)
    assert reuse_res.status_code in [400, 401]


@pytest.mark.asyncio
async def test_logout_invalidates_refresh_token(client: AsyncClient, registered_user: dict):
    """After logout, refresh token should be invalid."""
    # Login
    login_res = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    refresh_token = login_res.json()["data"]["refreshToken"]
    
    # Logout
    logout_res = await client.request(
        "DELETE",
        "/authentications/",
        json={"refreshToken": refresh_token}
    )
    assert logout_res.status_code == 200
    
    # Try to use the logged-out refresh token
    reuse_res = await client.put("/authentications/", json={
        "refreshToken": refresh_token
    })
    assert reuse_res.status_code in [400, 401]
