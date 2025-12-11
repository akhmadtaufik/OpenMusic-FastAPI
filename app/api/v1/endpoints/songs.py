"""Song endpoints for OpenMusic API (v1).

Provides CRUD operations for Song resources and list retrieval with optional
filters. Business logic is delegated to the SongService; responses use a
standardized envelope shape.
"""

from fastapi import APIRouter, Depends, status
from app.api import deps
from app.services.song_service import SongService
from app.schemas.song import (
    SongCreate, 
    SongUpdate, 
    SongListWrapper,
    SongDetailWrapper,
    SongIdWrapper,
    SongList,
    SongDetail
)
from app.schemas.album import StandardResponse

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[SongIdWrapper])
async def create_song(
    song_in: SongCreate,
    service: SongService = Depends(deps.get_song_service),
):
    """Create a new song.

    Args:
        song_in: Payload containing song fields such as title, year, etc.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[SongIdWrapper]: Response with the created song ID.
    """
    new_song = await service.create_song(song_in)
    return StandardResponse(
        status="success",
        data=SongIdWrapper(songId=new_song.id)
    )

@router.get("/", response_model=StandardResponse[SongListWrapper])
async def get_songs(
    service: SongService = Depends(deps.get_song_service),
    title: str = None,
    performer: str = None,
):
    """List songs with optional case-insensitive filters.

    Args:
        title: Optional filter by song title (partial, case-insensitive).
        performer: Optional filter by performer (partial, case-insensitive).
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[SongListWrapper]: Response with a list projection of songs.
    """
    songs = await service.get_songs(title=title, performer=performer)
    # Map to simplified SongList
    song_list = [SongList.model_validate(song) for song in songs]
    return StandardResponse(
        status="success",
        data=SongListWrapper(songs=song_list)
    )

@router.get("/{id}", response_model=StandardResponse[SongDetailWrapper])
async def get_song(
    id: str,
    service: SongService = Depends(deps.get_song_service),
):
    """Retrieve a song by its identifier.

    Args:
        id: Public song identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[SongDetailWrapper]: Response with full song details.
    """
    song = await service.get_song_by_id(id)
    return StandardResponse(
        status="success",
        data=SongDetailWrapper(song=SongDetail.model_validate(song))
    )

@router.put("/{id}", response_model=StandardResponse[None])
async def update_song(
    id: str,
    song_in: SongUpdate,
    service: SongService = Depends(deps.get_song_service),
):
    """Update a song's mutable fields.

    Args:
        id: Public song identifier.
        song_in: New values for song fields; unspecified fields remain unchanged.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    await service.update_song(id, song_in)
    return StandardResponse(
        status="success",
        message="Song updated"
    )

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_song(
    id: str,
    service: SongService = Depends(deps.get_song_service),
):
    """Delete a song by its identifier.

    Args:
        id: Public song identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    await service.delete_song(id)
    return StandardResponse(
        status="success",
        message="Song deleted"
    )
