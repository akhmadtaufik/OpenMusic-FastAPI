"""Top-level API router configuration for OpenMusic API (v1).

Aggregates endpoint routers under a common APIRouter. Each sub-router is
mounted with a path prefix and tag for OpenAPI grouping.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import albums, songs

api_router = APIRouter()
api_router.include_router(albums.router, prefix="/albums", tags=["albums"])
api_router.include_router(songs.router, prefix="/songs", tags=["songs"])
