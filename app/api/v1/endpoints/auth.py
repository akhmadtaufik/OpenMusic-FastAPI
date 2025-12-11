"""API Endpoints for Authentication.
"""

from fastapi import APIRouter, Depends, status
from app.api import deps
from app.schemas.auth import LoginPayload, RefreshTokenPayload
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def login(
    data: LoginPayload,
    service: AuthService = Depends(deps.get_auth_service),
):
    """Login a user."""
    tokens = await service.login(data)
    
    return {
        "status": "success",
        "data": {
            "accessToken": tokens.accessToken,
            "refreshToken": tokens.refreshToken
        }
    }

@router.put("/", response_model=dict)
async def refresh_access_token(
    data: RefreshTokenPayload,
    service: AuthService = Depends(deps.get_auth_service),
):
    """Refresh access token."""
    new_access_token = await service.refresh_token(data.refreshToken)
    
    return {
        "status": "success",
        "data": {
            "accessToken": new_access_token
        }
    }

@router.delete("/", response_model=dict)
async def logout(
    data: RefreshTokenPayload,
    service: AuthService = Depends(deps.get_auth_service),
):
    """Logout a user (revoke refresh token)."""
    await service.logout(data.refreshToken)
    
    return {
        "status": "success",
        "message": "Refresh token deleted successfully"
    }
