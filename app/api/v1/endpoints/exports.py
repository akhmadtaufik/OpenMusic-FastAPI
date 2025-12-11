"""API Endpoints for Exporting Playlists.

Provides endpoint to request playlist export via RabbitMQ.
"""

from fastapi import APIRouter, Depends, status, Request
from app.api.deps import get_current_user
from app.services.playlist_service import PlaylistService
from app.services.producer_service import producer_service, ProducerService
from pydantic import BaseModel, EmailStr
from app.core.exceptions import NotFoundError, ForbiddenError
from app.api import deps
from app.core.limiter import limiter

router = APIRouter()


async def get_playlist_service_for_exports(
    db=Depends(deps.get_db),
) -> PlaylistService:
    """Factory that allows test patching of PlaylistService within this module."""
    return PlaylistService(db)


def get_producer_service_for_exports() -> ProducerService:
    """Factory that allows test patching of producer_service within this module."""
    return producer_service


class ExportPlaylistRequest(BaseModel):
    """Request schema for playlist export."""
    targetEmail: EmailStr


@router.post(
    "/playlists/{playlistId}",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Export playlist",
    description="Queue a playlist export job to email the playlist content to targetEmail.",
    responses={
        403: {"description": "Forbidden - not owner"},
        404: {"description": "Playlist not found"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def export_playlist(
    request: Request,
    playlistId: str,
    payload: ExportPlaylistRequest,
    current_user: str = Depends(get_current_user),
    playlist_service: PlaylistService = Depends(get_playlist_service_for_exports),
    producer: ProducerService = Depends(get_producer_service_for_exports),
):
    """Request to export a playlist.
    
    Verifies ownership and sends a message to the 'export:playlist' queue.
    
    Args:
        playlistId: ID of the playlist to export.
        payload: Contains targetEmail.
        current_user: Authenticated user ID.
        db: Database session.
        
    Returns:
        Success message.
        
    Raises:
        403: If user is not the owner.
        404: If playlist not found.
    """
    # Check ownership/existence (using verify_playlist_access logic or similar)
    # Since verify_playlist_access might allow collaborators, we need strict ownership checking
    # First, get the playlist to check owner
    playlist = await playlist_service.get_playlist_by_id(playlistId)
    
    if not playlist:
        raise NotFoundError("Playlist not found")

    if playlist.owner != current_user:
        raise ForbiddenError("You are not entitled to access this resource")

    # Send message to queue
    message = {
        "playlistId": playlistId,
        "targetEmail": payload.targetEmail
    }
    
    await producer.send_message("export:playlist", message)
    
    return {
        "status": "success",
        "message": "Permintaan Anda sedang kami proses"
    }
