"""Service layer for Playlist operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy import select, delete, exists, func, desc
from sqlalchemy.orm import selectinload, joinedload
from app.models.playlist import Playlist
from app.models.playlist_song import PlaylistSong
from app.models.song import Song
from app.models.user import User
from app.models.collaboration import Collaboration
from app.models.playlist_activity import PlaylistActivity
from app.schemas.playlist import PlaylistCreate, PlaylistWithSongs
from app.core.exceptions import ValidationError, NotFoundError, OpenMusicException, ForbiddenError
from fastapi import status

class PlaylistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_playlist_access(self, playlist_id: str, user_id: str) -> None:
        """Verify if user is owner or collaborator.
        
        Raises:
            NotFoundError: If playlist not found.
            ForbiddenError: If access denied.
        """
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
        
        if playlist.owner == user_id:
            return # Owner has access

        # Check collaboration
        stmt_collab = select(exists().where(
            Collaboration.playlist_id == playlist_id,
            Collaboration.user_id == user_id
        ))
        result_collab = await self.db.execute(stmt_collab)
        if result_collab.scalar():
            return # Collaborator has access
            
        raise ForbiddenError("You are not entitled to access this resource")


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
        """Get playlists owned by OR shared with a user.
        
        Args:
            owner_id: ID of the user.
            
        Returns:
            List of dictionaries with id, name, and owner username.
        """
        stmt = (
            select(Playlist, User.username)
            .join(User, Playlist.owner == User.id)
            .outerjoin(Collaboration, Playlist.id == Collaboration.playlist_id)
            .where(
                (Playlist.owner == owner_id) | (Collaboration.user_id == owner_id)
            )
            .group_by(Playlist.id, User.username)
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
            owner_id: ID of the requesting user (Owner or Collaborator).
            
        Raises:
            NotFoundError: If playlist or song not found.
            ForbiddenError: If user is not authorized.
        """
        # Verify Access (Owner OR Collaborator)
        await self.verify_playlist_access(playlist_id, owner_id)

        # Verify Song
        stmt_song = select(Song).where(Song.id == song_id)
        result_song = await self.db.execute(stmt_song)
        if not result_song.scalar_one_or_none():
            raise NotFoundError("Song not found")

        # Add to Playlist (via PlaylistSong)
        playlist_song = PlaylistSong(playlist_id=playlist_id, song_id=song_id)
        self.db.add(playlist_song)
        
        # Log Activity
        activity = PlaylistActivity(
            playlist_id=playlist_id,
            user_id=owner_id,
            song_id=song_id,
            action="add"
        )
        self.db.add(activity)

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
        
        # Verify Access (Owner OR Collaborator)
        # Note: We already fetched playlist and owner logic above, but to be consistent with new requirement:
        # "GET /playlists/{id}/songs (Get Songs): Use New Logic (Owner OR Collaborator)."
        # But we already did a query. Let's reuse verify helper or just implement logic here efficiently.
        # Since we have the playlist object, let's just check owner then collaborator.
        if playlist.owner != owner_id:
             # Check collaboration
             stmt_collab = select(exists().where(
                Collaboration.playlist_id == playlist_id,
                Collaboration.user_id == owner_id
             ))
             result_collab = await self.db.execute(stmt_collab)
             if not result_collab.scalar():
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
            owner_id: ID of the requesting user (Owner or Collaborator).
             
        Raises:
            NotFoundError: If playlist not found.
            ForbiddenError: If user is not authorized.
        """
        # Verify Access (Owner OR Collaborator)
        await self.verify_playlist_access(playlist_id, owner_id)

        # Remove from PlaylistSong
        stmt_del = delete(PlaylistSong).where(
            PlaylistSong.playlist_id == playlist_id,
            PlaylistSong.song_id == song_id
        )
        await self.db.execute(stmt_del)
        
        # Log Activity
        activity = PlaylistActivity(
            playlist_id=playlist_id,
            user_id=owner_id,
            song_id=song_id,
            action="delete"
        )
        self.db.add(activity)
        
        await self.db.commit()

    async def get_playlist_activities(self, playlist_id: str, owner_id: str) -> list[dict]:
        """Get activities for a playlist.
        
        Args:
            playlist_id: ID of the playlist.
            owner_id: ID of the requesting user (Must be Owner).
            
        Returns:
            List of activities.
            
        Raises:
            NotFoundError: If playlist not found.
            ForbiddenError: If user is not the owner.
        """
        # Verify Playlist and Owner (Strict Ownership)
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
             raise ForbiddenError("You are not entitled to access this resource")
             
        # Get Activities
        stmt_act = (
            select(PlaylistActivity, User.username, Song.title)
            .join(User, PlaylistActivity.user_id == User.id)
            .join(Song, PlaylistActivity.song_id == Song.id)
            .where(PlaylistActivity.playlist_id == playlist_id)
            .order_by(PlaylistActivity.time)
        )
        result_act = await self.db.execute(stmt_act)
        
        activities = []
        for activity, username, title in result_act:
            activities.append({
                "username": username,
                "title": title,
                "action": activity.action,
                "time": activity.time.isoformat()
            })
            
        return activities
