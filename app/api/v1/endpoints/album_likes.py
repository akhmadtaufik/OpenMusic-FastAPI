"""API Endpoints for Album Likes with caching support.

Provides like/unlike/count operations for albums with Redis caching.
"""

from fastapi import APIRouter, Depends, status, Response
from app.api.deps import get_current_user
from app.services.like_service import LikeService
from app.services.cache_service import cache_service
from app.api import deps

router = APIRouter()

# Cache TTL: 30 minutes
CACHE_TTL = 1800


def get_likes_cache_key(album_id: str) -> str:
    """Generate cache key for album likes."""
    return f"likes:{album_id}"


@router.post("/{id}/likes", status_code=status.HTTP_201_CREATED, response_model=dict)
async def like_album(
    id: str,
    current_user: str = Depends(get_current_user),
    service: LikeService = Depends(deps.get_like_service),
):
    """Like an album.

    After successful like, invalidates the cache for this album's likes count.
    """
    await service.add_like(current_user, id)
    
    # Invalidate cache
    await cache_service.delete(get_likes_cache_key(id))
    
    return {
        "status": "success",
        "message": "Menyukai album"
    }


@router.delete("/{id}/likes", response_model=dict)
async def unlike_album(
    id: str,
    current_user: str = Depends(get_current_user),
    service: LikeService = Depends(deps.get_like_service),
):
    """Unlike an album.

    After successful unlike, invalidates the cache for this album's likes count.
    """
    await service.remove_like(current_user, id)
    
    # Invalidate cache
    await cache_service.delete(get_likes_cache_key(id))
    
    return {
        "status": "success",
        "message": "Batal menyukai album"
    }


@router.get("/{id}/likes", response_model=dict)
async def get_album_likes(
    id: str,
    response: Response,
    service: LikeService = Depends(deps.get_like_service),
):
    """Get the number of likes for an album (public).

    Uses Redis cache with 30-minute TTL. Sets X-Data-Source header
    to 'cache' when serving from cache.
    """
    cache_key = get_likes_cache_key(id)
    
    # Try cache first
    cached_count = await cache_service.get(cache_key)
    
    if cached_count is not None:
        # Cache hit
        response.headers["X-Data-Source"] = "cache"
        return {
            "status": "success",
            "data": {
                "likes": int(cached_count)
            }
        }
    
    # Cache miss - get from database
    count = await service.get_likes_count(id)
    
    # Store in cache
    await cache_service.set(cache_key, str(count), CACHE_TTL)
    
    return {
        "status": "success",
        "data": {
            "likes": count
        }
    }
