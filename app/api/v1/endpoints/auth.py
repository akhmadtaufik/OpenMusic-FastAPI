"""API Endpoints for Authentication.
"""

from fastapi import APIRouter, Depends, status, Request
from app.api import deps
from app.schemas.auth import LoginPayload, RefreshTokenPayload
from app.services.auth_service import AuthService
from app.core.limiter import limiter

router = APIRouter()

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Login",
    description="Authenticate user and return access/refresh tokens.",
    responses={401: {"description": "Invalid credentials"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
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

@router.put(
    "/",
    response_model=dict,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for new access and refresh tokens.",
    responses={401: {"description": "Invalid refresh token"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
async def refresh_access_token(
    request: Request,
    data: RefreshTokenPayload,
    service: AuthService = Depends(deps.get_auth_service),
):
    """Refresh tokens with token rotation."""
    tokens = await service.refresh_token(data.refreshToken)
    
    return {
        "status": "success",
        "data": {
            "accessToken": tokens.accessToken,
            "refreshToken": tokens.refreshToken
        }
    }

@router.delete(
    "/",
    response_model=dict,
    summary="Logout",
    description="Revoke a refresh token (logout).",
    responses={400: {"description": "Refresh token not found"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
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
