"""Authentication tests for OpenMusic API.

Covers user registration, login, token refresh, and logout flows.
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# USER REGISTRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Successful user registration returns 201 with userId."""
    payload = {
        "username": "newuser",
        "password": "newpass123",
        "fullname": "New User"
    }
    response = await client.post("/users/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "userId" in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, registered_user: dict):
    """Registering duplicate username returns 400."""
    payload = {
        "username": registered_user["username"],  # Already exists
        "password": "different123",
        "fullname": "Duplicate User"
    }
    response = await client.post("/users/", json=payload)
    
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "fail"


# ============================================================================
# LOGIN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    """Successful login returns access and refresh tokens."""
    payload = {
        "username": registered_user["username"],
        "password": registered_user["password"]
    }
    response = await client.post("/authentications/", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "accessToken" in data["data"]
    assert "refreshToken" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, registered_user: dict):
    """Invalid password returns 401."""
    payload = {
        "username": registered_user["username"],
        "password": "wrongpassword"
    }
    response = await client.post("/authentications/", json=payload)
    
    assert response.status_code == 401
    data = response.json()
    assert data["status"] == "fail"
    assert "invalid" in data["message"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Login with non-existent username returns 401."""
    payload = {
        "username": "nonexistent",
        "password": "somepassword"
    }
    response = await client.post("/authentications/", json=payload)
    
    assert response.status_code == 401


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, registered_user: dict):
    """Valid refresh token returns new access token."""
    # First login to get tokens
    login_res = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    refresh_token = login_res.json()["data"]["refreshToken"]
    
    # Refresh the token
    response = await client.put("/authentications/", json={
        "refreshToken": refresh_token
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "accessToken" in data["data"]


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    """Invalid refresh token returns 400/401."""
    response = await client.put("/authentications/", json={
        "refreshToken": "invalid.token.here"
    })
    
    assert response.status_code in [400, 401]


@pytest.mark.asyncio
async def test_refresh_fake_token(client: AsyncClient):
    """Fake but valid-looking JWT returns error."""
    # A properly formatted but fake JWT
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiJmYWtlLXVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.invalidsignature"
    response = await client.put("/authentications/", json={
        "refreshToken": fake_token
    })
    
    assert response.status_code in [400, 401]


# ============================================================================
# LOGOUT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, registered_user: dict):
    """Logout with valid refresh token succeeds."""
    # First login to get tokens
    login_res = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    refresh_token = login_res.json()["data"]["refreshToken"]
    
    # Logout using request() for DELETE with body
    response = await client.request(
        "DELETE",
        "/authentications/",
        json={"refreshToken": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_logout_then_refresh_fails(client: AsyncClient, registered_user: dict):
    """After logout, refresh with same token should fail."""
    # Login
    login_res = await client.post("/authentications/", json={
        "username": registered_user["username"],
        "password": registered_user["password"]
    })
    refresh_token = login_res.json()["data"]["refreshToken"]
    
    # Logout using request() for DELETE with body
    await client.request(
        "DELETE",
        "/authentications/",
        json={"refreshToken": refresh_token}
    )
    
    # Try to refresh with logged-out token
    response = await client.put("/authentications/", json={
        "refreshToken": refresh_token
    })
    
    assert response.status_code in [400, 401]
