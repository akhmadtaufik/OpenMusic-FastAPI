"""API Endpoints for Exporting Playlists.

Provides endpoint to request playlist export via RabbitMQ.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.playlist_service import PlaylistService
from app.services.producer_service import producer_service
from pydantic import BaseModel, EmailStr
from app.core.exceptions import NotFoundError, ForbiddenError

router = APIRouter()


class ExportPlaylistRequest(BaseModel):
    """Request schema for playlist export."""
    targetEmail: EmailStr


@router.post("/playlists/{playlistId}", status_code=status.HTTP_201_CREATED, response_model=dict)
async def export_playlist(
    playlistId: str,
    payload: ExportPlaylistRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    playlist_service = PlaylistService(db)
    
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
    
    await producer_service.send_message("export:playlist", message)
    
    return {
        "status": "success",
        "message": "Permintaan Anda sedang kami proses"
    }
