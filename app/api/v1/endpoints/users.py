"""API Endpoints for User management.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, status, Request
from app.api import deps
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.core.limiter import limiter

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def add_user(
    request: Request,
    data: UserCreate,
    service: Annotated[UserService, Depends(deps.get_user_service)],
):
    """Register a new user."""
    user_id = await service.add_user(data)
    
    return {
        "status": "success",
        "data": {
            "userId": user_id
        }
    }
