"""Song endpoints for OpenMusic API (v1).

Provides CRUD operations for Song resources and list retrieval with optional
filters. Business logic is delegated to the SongService; responses use a
standardized envelope shape.
"""

from fastapi import APIRouter, Depends, status, Query, Request
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
from app.utils.common import clean_string
from app.core.limiter import limiter

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[SongIdWrapper],
    summary="Create song",
    description="Create a new song and optionally associate it to an album.",
    responses={400: {"description": "Validation error"}, 404: {"description": "Album not found"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
async def create_song(
    request: Request,
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

@router.get(
    "/",
    response_model=StandardResponse[SongListWrapper],
    summary="List songs",
    description="List songs with optional title/performer filters (case-insensitive).",
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
async def get_songs(
    request: Request,
    service: SongService = Depends(deps.get_song_service),
    title: str | None = Query(None, max_length=100),
    performer: str | None = Query(None, max_length=100),
):
    """List songs with optional case-insensitive filters.

    Args:
        title: Optional filter by song title (partial, case-insensitive).
        performer: Optional filter by performer (partial, case-insensitive).
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[SongListWrapper]: Response with a list projection of songs.
    """
    if title is not None:
        title = clean_string(title, 100) or None
    if performer is not None:
        performer = clean_string(performer, 100) or None
    songs = await service.get_songs(title=title, performer=performer)
    # Map to simplified SongList
    song_list = [SongList.model_validate(song) for song in songs]
    return StandardResponse(
        status="success",
        data=SongListWrapper(songs=song_list)
    )

@router.get(
    "/{id}",
    response_model=StandardResponse[SongDetailWrapper],
    summary="Get song",
    description="Retrieve a single song by id.",
    responses={404: {"description": "Song not found"}},
)
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

@router.put(
    "/{id}",
    response_model=StandardResponse[None],
    summary="Update song",
    description="Update song fields by id.",
    responses={404: {"description": "Song not found"}},
)
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

@router.delete(
    "/{id}",
    response_model=StandardResponse[None],
    summary="Delete song",
    description="Delete a song by id.",
    responses={404: {"description": "Song not found"}},
)
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
