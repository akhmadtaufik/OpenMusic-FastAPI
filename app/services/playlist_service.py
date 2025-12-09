"""Service layer for Playlist operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload
from app.models.playlist import Playlist
from app.models.playlist_song import PlaylistSong
from app.models.song import Song
from app.models.user import User
from app.schemas.playlist import PlaylistCreate, PlaylistWithSongs
from app.core.exceptions import ValidationError, NotFoundError, OpenMusicException
from fastapi import status

class ForbiddenError(OpenMusicException):
    """Raised when access is denied."""
    pass

class PlaylistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_playlist(self, data: PlaylistCreate, owner_id: str) -> str:
        """Create a new playlist.
        
        Args:
            data: Playlist creation data.
            owner_id: ID of the user creating the playlist.
            
        Returns:
            The ID of the created playlist.
        """
        new_playlist = Playlist(
            name=data.name,
            owner=owner_id
        )
        self.db.add(new_playlist)
        await self.db.commit()
        await self.db.refresh(new_playlist)
        return new_playlist.id

    async def get_playlists(self, owner_id: str) -> list[dict]:
        """Get playlists owned by a user.
        
        Args:
            owner_id: ID of the owner.
            
        Returns:
            List of dictionaries with id, name, and owner username.
        """
        stmt = (
            select(Playlist, User.username)
            .join(User, Playlist.owner == User.id)
            .where(Playlist.owner == owner_id)
        )
        result = await self.db.execute(stmt)
        playlists_data = []
        for playlist, username in result:
             playlists_data.append({
                 "id": playlist.id,
                 "name": playlist.name,
                 "username": username
             })
        return playlists_data

    async def delete_playlist(self, playlist_id: str, owner_id: str) -> None:
        """Delete a playlist.
        
        Args:
            playlist_id: ID of the playlist.
            owner_id: ID of the requesting user.
            
        Raises:
            NotFoundError: If playlist not found.
            ForbiddenError: If user is not the owner.
        """
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
            raise ForbiddenError("You are not entitled to access this resource")
            
        await self.db.delete(playlist)
        await self.db.commit()

    async def add_song_to_playlist(self, playlist_id: str, song_id: str, owner_id: str) -> None:
        """Add a song to a playlist.
        
        Args:
            playlist_id: ID of the playlist.
            song_id: ID of the song.
            owner_id: ID of the requesting user.
            
        Raises:
            NotFoundError: If playlist or song not found.
            ForbiddenError: If user is not the owner.
        """
        # Verify Playlist and Owner
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
             raise ForbiddenError("You are not entitled to access this resource")

        # Verify Song
        stmt_song = select(Song).where(Song.id == song_id)
        result_song = await self.db.execute(stmt_song)
        if not result_song.scalar_one_or_none():
            raise NotFoundError("Song not found")

        # Add to Playlist (via PlaylistSong)
        # Check if already exists? (Optional, but good practice. Spec doesn't strictly say, but usually idempotent or error)
        # We will just insert.
        playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
        self.db.add(playlist_song)
        await self.db.commit()

    async def get_playlist_with_songs(self, playlist_id: str, owner_id: str) -> dict:
        """Get playlist details with songs.
        
        Args:
            playlist_id: ID of the playlist.
            owner_id: ID of the requesting user.
            
        Returns:
            Dictionary with playlist details and list of songs.
            
        Raises:
             NotFoundError: If playlist not found.
            ForbiddenError: If user is not the owner.
        """
        stmt = (
            select(Playlist, User.username)
            .join(User, Playlist.owner == User.id)
            .options(selectinload(Playlist.songs))
            .where(Playlist.id == playlist_id)
        )
        result = await self.db.execute(stmt)
        row = result.first() # Using first() directly on Result returns a Row or None
        
        if not row:
             raise NotFoundError("Playlist not found")

        playlist, username = row
        
        if playlist.owner != owner_id:
            raise ForbiddenError("You are not entitled to access this resource")
            
        songs_data = []
        for song in playlist.songs:
            songs_data.append({
                "id": song.id,
                "title": song.title,
                "performer": song.performer
            })
            
        return {
            "id": playlist.id,
            "name": playlist.name,
            "username": username,
            "songs": songs_data
        }

    async def delete_song_from_playlist(self, playlist_id: str, song_id: str, owner_id: str) -> None:
        """Remove a song from a playlist.
        
        Args:
            playlist_id: ID of the playlist.
            song_id: ID of the song.
            owner_id: ID of the requesting user.
             
        Raises:
            NotFoundError: If playlist not found.
            ForbiddenError: If user is not the owner.
        """
        # Verify Playlist and Owner
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
             raise ForbiddenError("You are not entitled to access this resource")

        # Remove from PlaylistSong
        stmt_del = delete(PlaylistSong).where(
            PlaylistSong.playlist_id == playlist_id,
            PlaylistSong.song_id == song_id
        )
        await self.db.execute(stmt_del)
        await self.db.commit()
