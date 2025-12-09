"""SQLAlchemy ORM model for Authentication.

Defines the Authentication table used for storing refresh tokens.
"""

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Authentication(Base):
    """Authentication entity mapped to the 'authentications' table.

    Attributes:
        token: Refund token string.
    """
    __tablename__ = "authentications"

    token: Mapped[str] = mapped_column(Text, primary_key=True)
