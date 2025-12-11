"""Common FastAPI dependencies for the API layer.

Currently exposes an async database session provider used by route handlers.
Sessions are opened and closed per-request using the project-wide session
factory.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.album_service import AlbumService
from app.services.song_service import SongService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.playlist_service import PlaylistService
from app.services.collaboration_service import CollaborationService
from app.services.like_service import LikeService
from app.services.producer_service import producer_service, ProducerService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session.

    This function is intended for FastAPI dependency injection. It opens an
    async session from the global factory and ensures proper cleanup once the
    request is finished.

    Yields:
        AsyncSession: The active database session for the request.
    """
    async with AsyncSessionLocal() as session:
        yield session

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_access_token


# Database dependency

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authentications")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Validate access token and return user ID."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_access_token(token)
    if not user_id:
        raise credentials_exception

    return user_id


# Service factories

async def get_album_service(db: AsyncSession = Depends(get_db)) -> AlbumService:
    return AlbumService(db)


async def get_song_service(db: AsyncSession = Depends(get_db)) -> SongService:
    return SongService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_playlist_service(db: AsyncSession = Depends(get_db)) -> PlaylistService:
    return PlaylistService(db)


async def get_collaboration_service(db: AsyncSession = Depends(get_db)) -> CollaborationService:
    return CollaborationService(db)


async def get_like_service(db: AsyncSession = Depends(get_db)) -> LikeService:
    return LikeService(db)


async def get_producer_service() -> ProducerService:
    return producer_service
