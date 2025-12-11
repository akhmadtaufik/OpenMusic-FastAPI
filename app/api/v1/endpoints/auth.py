"""API Endpoints for Authentication.
"""

from fastapi import APIRouter, Depends, status, Request
from app.api import deps
from app.schemas.auth import LoginPayload, RefreshTokenPayload
from app.services.auth_service import AuthService
from app.core.limiter import limiter

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def login(
    request: Request,
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
@limiter.limit("10/minute")
async def refresh_access_token(
    request: Request,
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
@limiter.limit("10/minute")
async def logout(
    request: Request,
    data: RefreshTokenPayload,
    service: AuthService = Depends(deps.get_auth_service),
):
    """Logout a user (revoke refresh token)."""
    await service.logout(data.refreshToken)
    
    return {
        "status": "success",
        "message": "Refresh token deleted successfully"
    }
