"""Top-level API router configuration for OpenMusic API (v1).

Aggregates endpoint routers under a common APIRouter. Each sub-router is
mounted with a path prefix and tag for OpenAPI grouping.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import albums, songs, users, auth, playlists, collaborations

api_router = APIRouter()
api_router.include_router(albums.router, prefix="/albums", tags=["albums"])
api_router.include_router(songs.router, prefix="/songs", tags=["songs"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/authentications", tags=["authentications"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(collaborations.router, prefix="/collaborations", tags=["collaborations"])
