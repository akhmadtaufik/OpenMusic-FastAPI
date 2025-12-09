"""Album endpoints for OpenMusic API (v1).

Exposes CRUD operations for Album resources. Each handler delegates business
logic to the AlbumService and returns standardized API envelopes.
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.album_service import AlbumService
from app.schemas.album import AlbumCreate, AlbumResponse, StandardResponse, DataWrapper, AlbumIdWrapper

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[AlbumIdWrapper])
async def create_album(
    album_in: AlbumCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """Create a new album.

    Args:
        album_in: Payload containing album name and year.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[AlbumIdWrapper]: Response with the created album ID.
    """
    service = AlbumService(db)
    new_album = await service.create_album(album_in)
    return StandardResponse(
        status="success",
        data=AlbumIdWrapper(albumId=new_album.id)
    )

@router.get("/{id}", response_model=StandardResponse[DataWrapper[AlbumResponse]])
async def get_album(
    id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """Retrieve an album by its identifier.

    Args:
        id: Public album identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[DataWrapper[AlbumResponse]]: Response with album data
        including its songs.
    """
    service = AlbumService(db)
    album = await service.get_album_by_id(id)
    return StandardResponse(
        status="success",
        data=DataWrapper(album=album)
    )

@router.put("/{id}", response_model=StandardResponse[None])
async def update_album(
    id: str,
    album_in: AlbumCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    """Update an album's mutable fields.

    Args:
        id: Public album identifier.
        album_in: New values for name and year.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    service = AlbumService(db)
    await service.update_album(id, album_in)
    return StandardResponse(
        status="success",
        message="Album updated"
    )

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_album(
    id: str,
    db: AsyncSession = Depends(deps.get_db)
):
    """Delete an album by its identifier.

    Args:
        id: Public album identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    service = AlbumService(db)
    await service.delete_album(id)
    return StandardResponse(
        status="success",
        message="Album deleted"
    )
