"""API Endpoints for Album Likes.

Provides like/unlike/count operations for albums.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services.like_service import LikeService

router = APIRouter()


@router.post("/{id}/likes", status_code=status.HTTP_201_CREATED, response_model=dict)
async def like_album(
    id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Like an album.

    Args:
        id: Album identifier.
        current_user: Authenticated user ID from token.
        db: Database session.

    Returns:
        Success response.

    Raises:
        400: If already liked.
        404: If album not found.
    """
    service = LikeService(db)
    await service.add_like(current_user, id)
    return {
        "status": "success",
        "message": "Menyukai album"
    }


@router.delete("/{id}/likes", response_model=dict)
async def unlike_album(
    id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unlike an album.

    Args:
        id: Album identifier.
        current_user: Authenticated user ID from token.
        db: Database session.

    Returns:
        Success response.
    """
    service = LikeService(db)
    await service.remove_like(current_user, id)
    return {
        "status": "success",
        "message": "Batal menyukai album"
    }


@router.get("/{id}/likes", response_model=dict)
async def get_album_likes(
    id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the number of likes for an album (public).

    Args:
        id: Album identifier.
        db: Database session.

    Returns:
        Success response with likes count.
    """
    service = LikeService(db)
    count = await service.get_likes_count(id)
    return {
        "status": "success",
        "data": {
            "likes": count
        }
    }
