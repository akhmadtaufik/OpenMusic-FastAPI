"""API Endpoints for Playlist management.
"""

from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistResponse,
    PlaylistSongRequest,
    PlaylistWithSongsResponse
)
from app.services.playlist_service import PlaylistService
from app.api import deps

router = APIRouter()

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_playlist(
    data: PlaylistCreate,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Create a new playlist."""
    playlist_id = await service.create_playlist(data, owner_id=current_user)
    
    return {
        "status": "success",
        "data": {
            "playlistId": playlist_id
        }
    }

@router.get("/", response_model=dict)
async def get_playlists(
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Get playlists owned by the current user."""
    playlists = await service.get_playlists(owner_id=current_user)
    
    return {
        "status": "success",
        "data": {
            "playlists": playlists
        }
    }

@router.delete("/{playlist_id}", response_model=dict)
async def delete_playlist(
    playlist_id: str,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Delete a playlist."""
    await service.delete_playlist(playlist_id, owner_id=current_user)
    
    return {
        "status": "success",
        "message": "Playlist deleted successfully"
    }

@router.post("/{playlist_id}/songs", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_song_to_playlist(
    playlist_id: str,
    data: PlaylistSongRequest,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Add a song to a playlist."""
    await service.add_song_to_playlist(playlist_id, data.songId, owner_id=current_user)
    
    return {
        "status": "success",
        "message": "Song added to playlist"
    }

@router.get("/{playlist_id}/songs", response_model=PlaylistWithSongsResponse)
async def get_playlist_songs(
    playlist_id: str,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Get playlist details with songs."""
    data = await service.get_playlist_with_songs(playlist_id, owner_id=current_user)
    
    # We need to wrap it to match the strict response format
    return {
        "status": "success",
        "data": {
            "playlist": data
        }
    }

@router.delete("/{playlist_id}/songs", response_model=dict)
async def delete_song_from_playlist(
    playlist_id: str,
    data: PlaylistSongRequest,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Remove a song from a playlist."""
    await service.delete_song_from_playlist(playlist_id, data.songId, owner_id=current_user)
    
    return {
        "status": "success",
        "message": "Song removed from playlist"
    }

@router.get("/{playlist_id}/activities", response_model=dict)
async def get_playlist_activities(
    playlist_id: str,
    current_user: str = Depends(get_current_user),
    service: PlaylistService = Depends(deps.get_playlist_service),
):
    """Get playlist activities."""
    activities = await service.get_playlist_activities(playlist_id, owner_id=current_user)
    
    return {
        "status": "success",
        "data": {
            "playlistId": playlist_id,
            "activities": activities
        }
    }
