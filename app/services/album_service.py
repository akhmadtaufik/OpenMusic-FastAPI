from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.album import Album
from app.schemas.album import AlbumCreate
from app.core.exceptions import NotFoundError

class AlbumService:
    """Service layer for Album domain operations.

    Encapsulates database interactions related to Album entities using an
    asynchronous SQLAlchemy session. Methods ensure albums are returned with
    their related songs eagerly loaded to avoid lazy-load issues in async
    contexts.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session.

        Args:
            db: Async SQLAlchemy session used to perform database operations.
        """
        self.db = db

    async def create_album(self, album_in: AlbumCreate) -> Album:
        """Create a new album and return it with songs relationship loaded.

        Uses selectinload to eagerly load the songs relationship after the
        insert to ensure the returned instance is safe for serialization in
        async contexts without triggering lazy loads.

        Args:
            album_in: Validated album payload.

        Returns:
            The persisted Album instance with songs preloaded.
        """
        album = Album(**album_in.model_dump())
        self.db.add(album)
        await self.db.commit()
        await self.db.refresh(album)
        # Manually set empty songs list to avoid lazy load error
        # or use selectinload to refresh
        # But refresh with relationships is tricky in async
        # Simple fix: explicit attribute set for pydantic
        # album.songs = [] 
        # Better: refresh with option
        result = await self.db.execute(
            select(Album)
            .options(selectinload(Album.songs))
            .where(Album.id == album.id)
        )
        return result.scalar_one()

    async def get_album_by_id(self, album_id: str) -> Album:
        """Fetch an album by ID with songs relationship loaded.

        Args:
            album_id: The album identifier.

        Returns:
            The Album instance with songs preloaded.

        Raises:
            NotFoundError: If the album does not exist.
        """
        result = await self.db.execute(
            select(Album)
            .options(selectinload(Album.songs))
            .where(Album.id == album_id)
        )
        album = result.scalar_one_or_none()
        if not album:
            raise NotFoundError("Album not found")
        return album

    async def update_album(self, album_id: str, album_in: AlbumCreate) -> None:
        """Update mutable fields on an album.

        Args:
            album_id: The target album identifier.
            album_in: Payload containing new values for name and year.
        """
        album = await self.get_album_by_id(album_id)
        album.name = album_in.name
        album.year = album_in.year
        await self.db.commit()

    async def delete_album(self, album_id: str) -> None:
        """Delete an album by its identifier.

        Args:
            album_id: The album identifier to remove.
        """
        album = await self.get_album_by_id(album_id)
        await self.db.delete(album)
        await self.db.commit()

    async def update_cover_url(self, album_id: str, cover_url: str) -> None:
        """Update the cover URL for an album.

        Args:
            album_id: The target album identifier.
            cover_url: The URL of the uploaded cover image.
        """
        album = await self.get_album_by_id(album_id)
        album.cover_url = cover_url
        await self.db.commit()
