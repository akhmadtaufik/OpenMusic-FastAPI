"""API Endpoints for User management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user."""
    service = UserService(db)
    user_id = await service.add_user(data)
    
    return {
        "status": "success",
        "data": {
            "userId": user_id
        }
    }
