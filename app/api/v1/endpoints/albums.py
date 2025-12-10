"""Album endpoints for OpenMusic API (v1).

Exposes CRUD operations for Album resources. Each handler delegates business
logic to the AlbumService and returns standardized API envelopes.
"""

import time
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.album_service import AlbumService
from app.services.storage_service import storage_service
from app.schemas.album import AlbumCreate, AlbumResponse, StandardResponse, DataWrapper, AlbumIdWrapper

router = APIRouter()

# Maximum file size: 512KB
MAX_FILE_SIZE = 512_000
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


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
    # Map cover_url to coverUrl for response
    album_response = AlbumResponse(
        id=album.id,
        name=album.name,
        year=album.year,
        coverUrl=album.cover_url,
        songs=album.songs
    )
    return StandardResponse(
        status="success",
        data=DataWrapper(album=album_response)
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


@router.post("/{id}/covers", status_code=status.HTTP_201_CREATED, response_model=StandardResponse[None])
async def upload_cover(
    id: str,
    cover: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db)
):
    """Upload a cover image for an album.

    Args:
        id: Public album identifier.
        cover: The uploaded image file (multipart/form-data).
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.

    Raises:
        HTTPException 400: If the file is not an image or exceeds 512KB.
        HTTPException 404: If the album does not exist.
    """
    # Validate content type
    if cover.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (jpeg, png, gif, webp)"
        )

    # Read and validate file size
    content = await cover.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({MAX_FILE_SIZE // 1000}KB)"
        )

    # Reset file position for upload
    await cover.seek(0)

    # Verify album exists
    service = AlbumService(db)
    await service.get_album_by_id(id)

    # Generate unique filename
    timestamp = int(time.time() * 1000)
    original_name = cover.filename or "cover"
    filename = f"covers/{id}/{timestamp}_{original_name}"

    # Upload to MinIO
    cover_url = await storage_service.upload_file(cover, filename)

    # Update album record
    await service.update_cover_url(id, cover_url)

    return StandardResponse(
        status="success",
        message="Sampul berhasil diunggah"
    )

