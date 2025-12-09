"""API Endpoints for Authentication.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.auth import LoginPayload, RefreshTokenPayload
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def login(
    data: LoginPayload,
    db: AsyncSession = Depends(get_db)
):
    """Login a user."""
    service = AuthService(db)
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
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token."""
    service = AuthService(db)
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
    db: AsyncSession = Depends(get_db)
):
    """Logout a user (revoke refresh token)."""
    service = AuthService(db)
    await service.logout(data.refreshToken)
    
    return {
        "status": "success",
        "message": "Refresh token deleted successfully"
    }
