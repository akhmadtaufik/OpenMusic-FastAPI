"""SQLAlchemy ORM model for PlaylistSong.

Defines the Many-to-Many relationship between Playlists and Songs.
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import shortuuid

def generate_playlist_song_id():
    """Generate a stable, prefixed random identifier for playlist songs."""
    return f"ps-{shortuuid.ShortUUID().random(length=16)}"

class PlaylistSong(Base):
    """PlaylistSong entity mapped to the 'playlist_songs' table.

    Attributes:
        id: Public-facing primary key.
        playlist_id: FK to playlists.
        song_id: FK to songs.
    """
    __tablename__ = "playlist_songs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_playlist_song_id)
    playlist_id: Mapped[str] = mapped_column(String, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    song_id: Mapped[str] = mapped_column(String, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
