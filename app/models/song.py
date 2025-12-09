"""SQLAlchemy ORM model for Song.

Defines the Song table, including an optional relationship to Album.
Public IDs use a short, prefixed random string for safe external exposure.
"""

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import shortuuid

def generate_song_id():
    """Generate a stable, prefixed random identifier for songs.

    Returns:
        str: An ID like 'song-<16-char random>', suitable for exposure in APIs.
    """
    return f"song-{shortuuid.ShortUUID().random(length=16)}"

class Song(Base):
    """Song entity mapped to the 'songs' table.

    Attributes:
        id: Public-facing primary key with 'song-' prefix.
        title: Song title.
        year: Release year of the song.
        genre: Music genre label.
        performer: Primary performer or artist.
        duration: Optional duration in seconds.
        albumId: Optional foreign key referencing Album.id; nullable for
            singles or unassigned songs.
        album: Relationship to Album; no cascade defined here since the
            Album side owns the lifecycle via delete-orphan.
    """
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_song_id)
    title: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[str] = mapped_column(String, nullable=False)
    performer: Mapped[str] = mapped_column(String, nullable=False)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    albumId: Mapped[str | None] = mapped_column(String, ForeignKey("albums.id"), nullable=True)

    # Bidirectional relationship; album owns cascade via its 'songs' rel.
    album = relationship("Album", back_populates="songs")
