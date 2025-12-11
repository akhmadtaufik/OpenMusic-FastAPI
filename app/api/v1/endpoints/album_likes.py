"""API Endpoints for Album Likes with caching support.

Provides like/unlike/count operations for albums with Redis caching.
"""

from fastapi import APIRouter, Depends, status, Response, Request
from app.api.deps import get_current_user
from app.services.like_service import LikeService
from app.services.cache_service import CacheService, cache_service
from app.api import deps
from app.core.limiter import limiter

router = APIRouter()


async def get_like_service_for_albums(db=Depends(deps.get_db)) -> LikeService:
    """Factory to allow tests to patch LikeService within this module."""
    return LikeService(db)


def get_cache_service_for_albums() -> CacheService:
    """Provide cache service (mockable in tests by patching cache_service)."""
    return cache_service

# Cache TTL: 30 minutes
CACHE_TTL = 1800


def get_likes_cache_key(album_id: str) -> str:
    """Generate cache key for album likes."""
    return f"likes:{album_id}"


@router.post(
    "/{id}/likes",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Like album",
    description="Like an album (invalidates cache).",
    responses={401: {"description": "Unauthorized"}, 404: {"description": "Album not found"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("30/minute")
async def like_album(
    request: Request,
    id: str,
    current_user: str = Depends(get_current_user),
    service: LikeService = Depends(get_like_service_for_albums),
    cache: CacheService = Depends(get_cache_service_for_albums),
):
    """Like an album.

    After successful like, invalidates the cache for this album's likes count.
    """
    await service.add_like(current_user, id)
    
    # Invalidate cache
    await cache.delete(get_likes_cache_key(id))
    
    return {
        "status": "success",
        "message": "Menyukai album"
    }


@router.delete(
    "/{id}/likes",
    response_model=dict,
    summary="Unlike album",
    description="Remove a like from an album (invalidates cache).",
    responses={401: {"description": "Unauthorized"}, 429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("30/minute")
async def unlike_album(
    request: Request,
    id: str,
    current_user: str = Depends(get_current_user),
    service: LikeService = Depends(get_like_service_for_albums),
    cache: CacheService = Depends(get_cache_service_for_albums),
):
    """Unlike an album.

    After successful unlike, invalidates the cache for this album's likes count.
    """
    await service.remove_like(current_user, id)
    
    # Invalidate cache
    await cache.delete(get_likes_cache_key(id))
    
    return {
        "status": "success",
        "message": "Batal menyukai album"
    }


@router.get(
    "/{id}/likes",
    response_model=dict,
    summary="Get album likes",
    description="Get album like count (cache-aside with Redis).",
    responses={429: {"description": "Rate limit exceeded"}},
)
@limiter.limit("100/minute")
async def get_album_likes(
    request: Request,
    id: str,
    response: Response,
    service: LikeService = Depends(get_like_service_for_albums),
    cache: CacheService = Depends(get_cache_service_for_albums),
):
    """Get the number of likes for an album (public).

    Uses Redis cache with 30-minute TTL (cache-aside pattern): try cache first,
    fall back to DB on miss, and write-through with TTL. Writes are invalidated
    on like/unlike endpoints to keep counts fresh.
    """
    cache_key = get_likes_cache_key(id)
    
    # Try cache first
    cached_count = await cache.get(cache_key)
    
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
    await cache.set(cache_key, str(count), CACHE_TTL)
    
    return {
        "status": "success",
        "data": {
            "likes": count
        }
    }
