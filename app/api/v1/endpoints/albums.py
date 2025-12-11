"""Album endpoints for OpenMusic API (v1).

Exposes CRUD operations for Album resources. Each handler delegates business
logic to the AlbumService and returns standardized API envelopes.
"""

import time
from fastapi import APIRouter, Depends, status, UploadFile, File, Request
from app.api import deps
from app.services.album_service import AlbumService
from app.services.storage_service import storage_service
from app.schemas.album import AlbumCreate, AlbumResponse, StandardResponse, DataWrapper, AlbumIdWrapper
from app.core.exceptions import ValidationError, PayloadTooLargeError
from app.utils.file_validator import validate_image_bytes
from app.core.limiter import limiter

router = APIRouter()

# Maximum file size: 512KB
MAX_FILE_SIZE = 512_000
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[AlbumIdWrapper],
    summary="Create album",
    description="Create a new album with name and year.",
    responses={400: {"description": "Validation error"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("50/minute")
async def create_album(
    request: Request,
    album_in: AlbumCreate,
    service: AlbumService = Depends(deps.get_album_service),
):
    """Create a new album.

    Args:
        album_in: Payload containing album name and year.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[AlbumIdWrapper]: Response with the created album ID.
    """
    new_album = await service.create_album(album_in)
    return StandardResponse(
        status="success",
        data=AlbumIdWrapper(albumId=new_album.id)
    )

@router.get(
    "/{id}",
    response_model=StandardResponse[DataWrapper[AlbumResponse]],
    summary="Get album",
    description="Retrieve album detail including songs and cover URL.",
    responses={404: {"description": "Album not found"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
async def get_album(
    request: Request,
    id: str,
    service: AlbumService = Depends(deps.get_album_service),
):
    """Retrieve an album by its identifier.

    Args:
        id: Public album identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[DataWrapper[AlbumResponse]]: Response with album data
        including its songs.
    """
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
    service: AlbumService = Depends(deps.get_album_service),
):
    """Update an album's mutable fields.

    Args:
        id: Public album identifier.
        album_in: New values for name and year.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    await service.update_album(id, album_in)
    return StandardResponse(
        status="success",
        message="Album updated"
    )

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_album(
    id: str,
    service: AlbumService = Depends(deps.get_album_service),
):
    """Delete an album by its identifier.

    Args:
        id: Public album identifier.
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.
    """
    await service.delete_album(id)
    return StandardResponse(
        status="success",
        message="Album deleted"
    )


@router.post(
    "/{id}/covers",
    status_code=status.HTTP_201_CREATED,
    response_model=StandardResponse[None],
    summary="Upload album cover",
    description="Upload an image cover (PNG/JPEG/GIF/WebP, magic-number validated).",
    responses={
        400: {"description": "Invalid file or payload"},
        403: {"description": "Forbidden"},
        404: {"description": "Album not found"},
        413: {"description": "Payload too large"},
        429: {"description": "Rate limit exceeded"},
    },
)
@limiter.limit("10/minute")
async def upload_cover(
    request: Request,
    id: str,
    service: AlbumService = Depends(deps.get_album_service),
    cover: UploadFile = File(...),
):
    """Upload a cover image for an album.

    Args:
        id: Public album identifier.
        cover: The uploaded image file (multipart/form-data).
        db: Async SQLAlchemy session provided by dependency injection.

    Returns:
        StandardResponse[None]: Response with a success status and message.

    Raises:
        ValidationError: If the file is not an image.
        PayloadTooLargeError: If the file exceeds 512KB.
        NotFoundError: If the album does not exist.
    """
    # Validate content type
    # Read and validate file size
    content = await cover.read()
    if len(content) > MAX_FILE_SIZE:
        raise PayloadTooLargeError(f"File size exceeds maximum allowed ({MAX_FILE_SIZE // 1000}KB)")

    validate_image_bytes(cover.filename or "cover", content)

    # Reset file position for upload
    await cover.seek(0)

    # Verify album exists
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

