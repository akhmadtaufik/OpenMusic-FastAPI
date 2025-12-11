"""API Endpoints for Collaboration management.
"""

from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.services.collaboration_service import CollaborationService
from pydantic import BaseModel
from app.api import deps

router = APIRouter()

class CollaborationPayload(BaseModel):
    playlistId: str
    userId: str

@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add collaboration",
    description="Add a collaborator to a playlist (owner only).",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
)
async def add_collaboration(
    data: CollaborationPayload,
    current_user: str = Depends(get_current_user),
    service: CollaborationService = Depends(deps.get_collaboration_service),
):
    """Add a collaborator to a playlist."""
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

@router.delete(
    "/",
    response_model=dict,
    summary="Delete collaboration",
    description="Remove a collaborator from a playlist (owner only).",
    responses={401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 404: {"description": "Not found"}},
)
async def delete_collaboration(
    data: CollaborationPayload,
    current_user: str = Depends(get_current_user),
    service: CollaborationService = Depends(deps.get_collaboration_service),
):
    """Remove a collaborator from a playlist."""
    await service.delete_collaboration(
        playlist_id=data.playlistId,
        user_id=data.userId,
        owner_id=current_user
    )
    
    return {
        "status": "success",
        "message": "Collaborator removed successfully"
    }
