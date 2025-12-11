"""Service for album like operations.

Handles add/remove/count operations for album likes using the UserAlbumLike model.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from app.models.user_album_like import UserAlbumLike
from app.models.album import Album
from app.core.exceptions import NotFoundError, ValidationError


class LikeService:
    """Service layer for album like operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session."""
        self.db = db

    async def _check_album_exists(self, album_id: str) -> None:
        """Verify album exists, raise 404 if not."""
        result = await self.db.execute(
            select(Album).where(Album.id == album_id)
        )
        if not result.scalar_one_or_none():
            raise NotFoundError("Album not found")

    async def add_like(self, user_id: str, album_id: str) -> None:
        """Add a like to an album.

        Args:
            user_id: The ID of the user liking the album.
            album_id: The ID of the album to like.

        Raises:
            NotFoundError: If album doesn't exist.
            ValidationError: If user already liked this album.
        """
        await self._check_album_exists(album_id)

        # Check if already liked
        result = await self.db.execute(
            select(UserAlbumLike).where(
                UserAlbumLike.user_id == user_id,
                UserAlbumLike.album_id == album_id
            )
        )
        if result.scalar_one_or_none():
            raise ValidationError("You have already liked this album")

        # Create like
        like = UserAlbumLike(user_id=user_id, album_id=album_id)
        self.db.add(like)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValidationError("You have already liked this album")

    async def remove_like(self, user_id: str, album_id: str) -> None:
        """Remove a like from an album (idempotent).

        Args:
            user_id: The ID of the user unliking the album.
            album_id: The ID of the album to unlike.
        """
        await self.db.execute(
            delete(UserAlbumLike).where(
                UserAlbumLike.user_id == user_id,
                UserAlbumLike.album_id == album_id
            )
        )
        await self.db.commit()

    async def get_likes_count(self, album_id: str) -> int:
        """Get the total number of likes for an album.

        Args:
            album_id: The ID of the album.

        Returns:
            int: The number of likes.
        """
        result = await self.db.execute(
            select(func.count()).select_from(UserAlbumLike).where(
                UserAlbumLike.album_id == album_id
            )
        )
        return result.scalar() or 0
