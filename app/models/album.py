"""SQLAlchemy ORM model for Album.

Defines the Album table and relationships. IDs use a short, prefixed random
string suitable for external references.
"""

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import shortuuid

def generate_album_id():
    """Generate a stable, prefixed random identifier for albums.

    Returns:
        str: An ID like 'album-<16-char random>', suitable for exposure in APIs.
    """
    return f"album-{shortuuid.ShortUUID().random(length=16)}"

class Album(Base):
    """Album entity mapped to the 'albums' table.

    Attributes:
        id: Public-facing primary key with 'album-' prefix.
        name: Album title.
        year: Release year.
        songs: Relationship to Song with delete-orphan cascade to keep
            referential integrity when an album is removed.
    """
    __tablename__ = "albums"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_album_id)
    name: Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Cascade deletes to child songs so removing an album cleans up its rows.
    songs = relationship("Song", back_populates="album", cascade="all, delete-orphan")
