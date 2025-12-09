"""SQLAlchemy ORM model for Playlist.

Defines the Playlist table and relationships.
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import shortuuid

def generate_playlist_id():
    """Generate a stable, prefixed random identifier for playlists."""
    return f"playlist-{shortuuid.ShortUUID().random(length=16)}"

class Playlist(Base):
    """Playlist entity mapped to the 'playlists' table.

    Attributes:
        id: Public-facing primary key with 'playlist-' prefix.
        name: Name of the playlist.
        owner: Foreign key to the owner (User).
    """
    __tablename__ = "playlists"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_playlist_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    owner: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationship to user
    user = relationship("User", backref="playlists")

    # Relationship to songs (Many-to-Many via PlaylistSong)
    songs = relationship("Song", secondary="playlist_songs", backref="playlists", lazy="selectin")
