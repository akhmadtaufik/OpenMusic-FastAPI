"""Pydantic schemas for Song payloads and API response shapes.

Defines input/output models, list/detail projections, and small wrappers used
by the API layer. Models support construction from ORM objects where noted.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# Base
class SongBase(BaseModel):
    """Common fields shared by song create/update and response models."""
    title: str
    year: int
    genre: str
    performer: str
    duration: Optional[int] = None
    albumId: Optional[str] = None

# Create/Update
class SongCreate(SongBase):
    """Input payload for creating a new song."""
    pass

class SongUpdate(SongBase):
    """Input payload for updating an existing song."""
    pass

# Responses
class SongDetail(SongBase):
    """Full song representation returned by the API.

    Includes all base fields plus the public identifier.

    Notes:
        model_config.from_attributes=True enables construction from ORM
        entities (SQLAlchemy models) via attribute access.
    """
    id: str
    
    model_config = ConfigDict(from_attributes=True)

class SongList(BaseModel):
    """Projection for listing songs with minimal fields."""
    id: str
    title: str
    performer: str

    model_config = ConfigDict(from_attributes=True)

class SongSimplified(BaseModel):
    """Compact song shape embedded inside Album responses."""
    id: str
    title: str
    performer: str

    model_config = ConfigDict(from_attributes=True)

class SongId(BaseModel):
    """Response payload carrying only a song identifier."""
    songId: str

# Data Wrappers for StandardResponse
class SongListWrapper(BaseModel):
    """Wrapper used for responses with a 'songs' array payload."""
    songs: List[SongList]

class SongDetailWrapper(BaseModel):
    """Wrapper used for responses containing a single song payload."""
    song: SongDetail

class SongIdWrapper(BaseModel):
    """Wrapper used for responses returning only the created song ID."""
    songId: str
