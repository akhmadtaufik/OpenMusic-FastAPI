"""SQLAlchemy ORM model for Collaboration.

Defines the relationship between Playlists and Collaborating Users.
"""

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import shortuuid

def generate_collaboration_id():
    """Generate a stable, prefixed random identifier for collaborations."""
    return f"collab-{shortuuid.ShortUUID().random(length=16)}"

class Collaboration(Base):
    """Collaboration entity mapped to the 'collaborations' table.

    Attributes:
        id: Public-facing primary key.
        playlist_id: FK to playlists.
        user_id: FK to users (collaborator).
    """
    __tablename__ = "collaborations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_collaboration_id)
    playlist_id: Mapped[str] = mapped_column(String, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('playlist_id', 'user_id', name='unique_playlist_user'),
    )
