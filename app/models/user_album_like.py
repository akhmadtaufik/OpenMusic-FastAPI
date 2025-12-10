"""SQLAlchemy ORM model for UserAlbumLike.

Defines the many-to-many relationship between users and albums for the
"like" feature. Includes a unique constraint to prevent duplicate likes.
"""

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import shortuuid


def generate_like_id():
    """Generate a stable, prefixed random identifier for likes."""
    return f"like-{shortuuid.ShortUUID().random(length=16)}"


class UserAlbumLike(Base):
    """UserAlbumLike entity mapped to the 'user_album_likes' table.

    Represents a user's "like" on an album. The unique constraint on
    (user_id, album_id) ensures a user can only like an album once.

    Attributes:
        id: Public-facing primary key with 'like-' prefix.
        user_id: Foreign key to the user who liked the album.
        album_id: Foreign key to the liked album.
    """
    __tablename__ = "user_album_likes"
    __table_args__ = (
        UniqueConstraint('user_id', 'album_id', name='uq_user_album_like'),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_like_id)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    album_id: Mapped[str] = mapped_column(
        String, ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
