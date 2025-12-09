"""Integration tests for Album endpoints.

Covers happy paths and error handling for create and retrieve operations,
validating HTTP statuses and standardized response shapes.
"""

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_album(client: AsyncClient):
    """Create album returns 201 and the new albumId in the standard envelope."""
    payload = {"name": "Test Album", "year": 2023}
    response = await client.post("/albums/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "albumId" in data["data"]

@pytest.mark.asyncio
async def test_create_album_invalid_payload(client: AsyncClient):
    """Invalid payload yields 400 with a validation failure message."""
    payload = {"year": 2023} # Missing name
    response = await client.post("/albums/", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "fail"
    assert "Validation Error" in data["message"]

@pytest.mark.asyncio
async def test_get_album(client: AsyncClient):
    """Retrieve an existing album returns 200 with album data populated."""
    # First create an album
    payload = {"name": "Test Album", "year": 2023}
    create_res = await client.post("/albums/", json=payload)
    album_id = create_res.json()["data"]["albumId"]

    # Get the album
    response = await client.get(f"/albums/{album_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["album"]["id"] == album_id
    assert data["data"]["album"]["name"] == "Test Album"

@pytest.mark.asyncio
async def test_get_album_not_found(client: AsyncClient):
    """Unknown album ID returns 404 with a not-found message."""
    response = await client.get("/albums/album-nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == "fail"
    assert "not found" in data["message"].lower()
