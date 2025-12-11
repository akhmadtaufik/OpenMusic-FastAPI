"""Pydantic schemas for Song payloads and API response shapes.

Defines input/output models, list/detail projections, and small wrappers used
by the API layer. Models support construction from ORM objects where noted.
"""

from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Optional, List

# Base
class SongBase(BaseModel):
    """Common fields shared by song create/update and response models."""
    title: str = Field(..., example="Life in Technicolor")
    year: int = Field(..., example=2008)
    genre: str = Field(..., example="Alternative")
    performer: str = Field(..., example="Coldplay")
    duration: Optional[int] = Field(default=None, example=210)
    albumId: Optional[str] = Field(default=None, example="album-123")

    @field_validator("title", "genre", "performer")
    @classmethod
    def validate_str_fields(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be empty")
        if len(v) > 100:
            raise ValueError("Field must be at most 100 characters")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Year must be positive")
        return v

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Duration must be non-negative")
        return v

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
    id: str = Field(..., example="song-123")
    
    model_config = ConfigDict(from_attributes=True)

class SongList(BaseModel):
    """Projection for listing songs with minimal fields."""
    id: str = Field(..., example="song-123")
    title: str = Field(..., example="Life in Technicolor")
    performer: str = Field(..., example="Coldplay")

    model_config = ConfigDict(from_attributes=True)

class SongSimplified(BaseModel):
    """Compact song shape embedded inside Album responses."""
    id: str = Field(..., example="song-123")
    title: str = Field(..., example="Life in Technicolor")
    performer: str = Field(..., example="Coldplay")

    model_config = ConfigDict(from_attributes=True)

class SongId(BaseModel):
    """Response payload carrying only a song identifier."""
    songId: str = Field(..., example="song-123")

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
