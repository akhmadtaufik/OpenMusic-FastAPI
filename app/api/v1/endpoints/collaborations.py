"""API Endpoints for Collaboration management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.collaboration_service import CollaborationService
from pydantic import BaseModel

router = APIRouter()

class CollaborationPayload(BaseModel):
    playlistId: str
    userId: str

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_collaboration(
    data: CollaborationPayload,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a collaborator to a playlist."""
    service = CollaborationService(db)
    collab_id = await service.add_collaboration(
        playlist_id=data.playlistId,
        user_id=data.userId,
        owner_id=current_user
    )
    
    return {
        "status": "success",
        "data": {
            "collaborationId": collab_id
        }
    }

@router.delete("/", response_model=dict)
async def delete_collaboration(
    data: CollaborationPayload,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove a collaborator from a playlist."""
    service = CollaborationService(db)
    await service.delete_collaboration(
        playlist_id=data.playlistId,
        user_id=data.userId,
        owner_id=current_user
    )
    
    return {
        "status": "success",
        "message": "Collaborator removed successfully"
    }
