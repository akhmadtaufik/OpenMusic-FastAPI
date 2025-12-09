"""SQLAlchemy ORM model for User.

Defines the User table. IDs use a short, prefixed random string.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import shortuuid

def generate_user_id():
    """Generate a stable, prefixed random identifier for users."""
    return f"user-{shortuuid.ShortUUID().random(length=16)}"

class User(Base):
    """User entity mapped to the 'users' table.

    Attributes:
        id: Public-facing primary key with 'user-' prefix.
        username: Unique username for login.
        password: Hashed password.
        fullname: Full name of the user.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_user_id)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    fullname: Mapped[str] = mapped_column(String, nullable=False)
