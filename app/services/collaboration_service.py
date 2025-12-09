"""Service layer for Collaboration operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.collaboration import Collaboration
from app.models.playlist import Playlist
from app.models.user import User
from app.core.exceptions import NotFoundError, ValidationError, OpenMusicException, ForbiddenError

class CollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_collaboration(self, playlist_id: str, user_id: str, owner_id: str) -> str:
        """Add a collaborator to a playlist.
        
        Args:
            playlist_id: ID of the playlist.
            user_id: ID of the user to become collaborator.
            owner_id: ID of the playlist owner (requesting user).
            
        Returns:
            The ID of the created collaboration.
            
        Raises:
            NotFoundError: Playlist or User not found.
            ForbiddenError: Requesting user is not the owner.
        """
        # Verify Playlist and Owner
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
            raise ForbiddenError("You are not entitled to access this resource")
            
        # Verify User exists
        stmt_user = select(User).where(User.id == user_id)
        result_user = await self.db.execute(stmt_user)
        if not result_user.scalar_one_or_none():
            raise NotFoundError("User not found")

        # Check existing (optional, constraint handles it but cleaner logic)
        stmt_collab = select(Collaboration).where(
            Collaboration.playlist_id == playlist_id,
            Collaboration.user_id == user_id
        )
        result_collab = await self.db.execute(stmt_collab)
        if result_collab.scalar_one_or_none():
            # Already collaborator, return existing ID or raise specific error?
            # We'll just return the existing one or raise validation.
            # Returning existing ID is idempotent. But let's raise for clarity if needed.
            # For this task, let's just proceed to insert and catch integrity error OR just return existing.
            # Let's simple insert and let DB handle unique constraint if we didn't check.
            # Since we checked, we can just return existing ID or fail.
            # Requirement says "Insert into collaborations".
            # Let's assume standard behavior: if exists, fail? Or success?
            # Standard idempotent API: success.
            return result_collab.scalar_one().id

        new_collab = Collaboration(playlist_id=playlist_id, user_id=user_id)
        self.db.add(new_collab)
        await self.db.commit()
        await self.db.refresh(new_collab)
        
        return new_collab.id

    async def delete_collaboration(self, playlist_id: str, user_id: str, owner_id: str) -> None:
        """Remove a collaborator.
        
        Args:
           playlist_id: ID of the playlist.
           user_id: ID of the collaborator.
           owner_id: ID of the playlist owner.
        """
        # Verify Playlist and Owner
        stmt = select(Playlist).where(Playlist.id == playlist_id)
        result = await self.db.execute(stmt)
        playlist = result.scalar_one_or_none()
        
        if not playlist:
            raise NotFoundError("Playlist not found")
            
        if playlist.owner != owner_id:
            raise ForbiddenError("You are not entitled to access this resource")

        # Delete
        stmt_del = delete(Collaboration).where(
            Collaboration.playlist_id == playlist_id,
            Collaboration.user_id == user_id
        )
        await self.db.execute(stmt_del)
        await self.db.commit()
