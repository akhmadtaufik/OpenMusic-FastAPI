"""Collaboration tests for OpenMusic API.

Covers adding/removing collaborators and collaborator access permissions.
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# ADD COLLABORATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_add_collaborator_owner(
    client: AsyncClient,
    auth_headers: dict,
    sample_playlist: dict,
    second_user: dict
):
    """Owner can add collaborator to their playlist."""
    payload = {
        "playlistId": sample_playlist["id"],
        "userId": second_user["userId"]
    }
    response = await client.post(
        "/collaborations/",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert "collaborationId" in response.json()["data"]


@pytest.mark.asyncio
async def test_add_collaborator_non_owner(
    client: AsyncClient,
    sample_playlist: dict,
    second_auth_headers: dict,
    registered_user: dict
):
    """Non-owner cannot add collaborator (returns 403)."""
    payload = {
        "playlistId": sample_playlist["id"],
        "userId": registered_user["userId"]  # Try to add first user as collab
    }
    response = await client.post(
        "/collaborations/",
        json=payload,
        headers=second_auth_headers
    )
    
    assert response.status_code == 403


# ============================================================================
# COLLABORATOR ACCESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_collaborator_can_add_song(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    sample_playlist: dict,
    sample_song: dict,
    second_user: dict
):
    """Collaborator can add song to playlist after being added."""
    # Owner adds second user as collaborator
    await client.post(
        "/collaborations/",
        json={"playlistId": sample_playlist["id"], "userId": second_user["userId"]},
        headers=auth_headers
    )
    
    # Collaborator adds song
    response = await client.post(
        f"/playlists/{sample_playlist['id']}/songs",
        json={"songId": sample_song["id"]},
        headers=second_auth_headers
    )
    
    assert response.status_code == 201


# ============================================================================
# REMOVE COLLABORATOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_remove_collaborator_owner(
    client: AsyncClient,
    auth_headers: dict,
    sample_playlist: dict,
    second_user: dict
):
    """Owner can remove collaborator."""
    # First add collaborator
    await client.post(
        "/collaborations/",
        json={"playlistId": sample_playlist["id"], "userId": second_user["userId"]},
        headers=auth_headers
    )
    
    # Remove collaborator
    response = await client.request(
        "DELETE",
        "/collaborations/",
        json={"playlistId": sample_playlist["id"], "userId": second_user["userId"]},
        headers=auth_headers
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_removed_collaborator_loses_access(
    client: AsyncClient,
    auth_headers: dict,
    second_auth_headers: dict,
    sample_playlist: dict,
    sample_song: dict,
    second_user: dict
):
    """After removal, collaborator cannot add songs."""
    # Add then remove collaborator
    await client.post(
        "/collaborations/",
        json={"playlistId": sample_playlist["id"], "userId": second_user["userId"]},
        headers=auth_headers
    )
    await client.request(
        "DELETE",
        "/collaborations/",
        json={"playlistId": sample_playlist["id"], "userId": second_user["userId"]},
        headers=auth_headers
    )
    
    # Ex-collaborator tries to add song
    response = await client.post(
        f"/playlists/{sample_playlist['id']}/songs",
        json={"songId": sample_song["id"]},
        headers=second_auth_headers
    )
    
    assert response.status_code == 403
