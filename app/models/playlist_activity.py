"""SQLAlchemy ORM model for PlaylistActivity.

Defines the log for playlist actions.
"""

from sqlalchemy import String, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import shortuuid
from datetime import datetime

def generate_activity_id():
    """Generate a stable, prefixed random identifier for activities."""
    return f"activity-{shortuuid.ShortUUID().random(length=16)}"

class PlaylistActivity(Base):
    """PlaylistActivity entity mapped to the 'playlist_song_activities' table.

    Attributes:
        id: Public-facing primary key.
        playlist_id: FK to playlists.
        user_id: The ID of the user who performed the action (No strict FK needed for logs, but good for integrity).
                 We'll assume strict FK for consistency.
        song_id: ID of the song (soft link, not cascading delete to keep history).
        action: 'add' or 'delete'.
        time: Timestamp of action.
    """
    __tablename__ = "playlist_song_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_activity_id)
    playlist_id: Mapped[str] = mapped_column(String, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False) # Keep logs even if user deleted? Or cascade? Spec implies standard Foreign Key.
    song_id: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
