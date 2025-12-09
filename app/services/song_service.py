from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Sequence
from app.models.song import Song
from app.schemas.song import SongCreate, SongUpdate
from app.core.exceptions import NotFoundError

class SongService:
    """Service layer for Song domain operations.

    Encapsulates async SQLAlchemy interactions for Song entities. This layer
    centralizes business logic for creating, querying, updating and deleting
    songs, keeping endpoint handlers thin and focused on I/O concerns.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the service with a database session.

        Args:
            db: Async SQLAlchemy session used to perform database operations.
        """
        self.db = db

    async def create_song(self, song_in: SongCreate) -> Song:
        """Persist a new song.

        Args:
            song_in: Validated payload containing song attributes.

        Returns:
            The persisted Song instance.
        """
        song = Song(**song_in.model_dump())
        self.db.add(song)
        await self.db.commit()
        await self.db.refresh(song)
        return song

    async def get_songs(self, title: str | None = None, performer: str | None = None) -> Sequence[Song]:
        """Retrieve songs with optional case-insensitive filtering.

        Applies ILIKE filters when title or performer are provided. Filters are
        combined with AND semantics.

        Args:
            title: Optional partial title to match (case-insensitive, contains).
            performer: Optional partial performer to match (case-insensitive, contains).

        Returns:
            A list of matching Song instances, possibly empty.
        """
        query = select(Song)
        
        if title:
            query = query.where(Song.title.ilike(f"%{title}%"))
        
        if performer:
            query = query.where(Song.performer.ilike(f"%{performer}%"))
            
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_song_by_id(self, song_id: str) -> Song:
        """Fetch a song by its identifier.

        Args:
            song_id: The song identifier.

        Returns:
            The Song instance if found.

        Raises:
            NotFoundError: If the song does not exist.
        """
        result = await self.db.execute(select(Song).where(Song.id == song_id))
        song = result.scalar_one_or_none()
        if not song:
            raise NotFoundError("Song not found")
        return song

    async def update_song(self, song_id: str, song_in: SongUpdate) -> None:
        """Update a song's mutable fields.

        Performs a partial update using only fields provided in the payload.

        Args:
            song_id: The target song identifier.
            song_in: Payload with fields to update; unspecified fields are left unchanged.
        """
        song = await self.get_song_by_id(song_id)
        
        update_data = song_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(song, key, value)
            
        await self.db.commit()

    async def delete_song(self, song_id: str) -> None:
        """Delete a song by its identifier.

        Args:
            song_id: The song identifier to remove.
        """
        song = await self.get_song_by_id(song_id)
        await self.db.delete(song)
        await self.db.commit()
