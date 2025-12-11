"""Pydantic schemas for Album payloads and standard API envelopes.

Defines input/output models used by the API layer, including typed wrappers
for response shapes and attribute-based ORM serialization.
"""

from pydantic import BaseModel, ConfigDict, field_validator, Field
from typing import Generic, TypeVar, Optional, List
from app.schemas.song import SongSimplified

T = TypeVar('T')

class AlbumCreate(BaseModel):
    """Payload to create or update an album.

    Attributes:
        name: Album title.
        year: Release year.
    """
    name: str = Field(..., example="In Rainbows")
    year: int = Field(..., example=2007)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Album name must not be empty")
        if len(v) > 100:
            raise ValueError("Album name must be at most 100 characters")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Year must be positive")
        return v

class AlbumResponse(BaseModel):
    """Serialized album representation returned by the API.

    Attributes:
        id: Public album identifier.
        name: Album title.
        year: Release year.
        coverUrl: URL to the album cover image (if uploaded).
        songs: Collection of related songs in simplified form.

    Notes:
        model_config.from_attributes=True enables constructing this model
        directly from ORM entities (SQLAlchemy models) via attribute access.
    """
    id: str
    name: str = Field(..., example="In Rainbows")
    year: int = Field(..., example=2007)
    coverUrl: Optional[str] = Field(default=None, example="http://minio:9000/openmusic/covers/abc.png")
    songs: List[SongSimplified] = []

    model_config = ConfigDict(from_attributes=True)

class DataWrapper(BaseModel, Generic[T]):
    """Data container for 'album' namespaced payloads.

    Used to shape responses like {"data": {"album": <AlbumResponse>}} when
    combined with StandardResponse.
    """
    album: Optional[T] = None

class AlbumIdWrapper(BaseModel):
    """Response payload carrying only an album identifier.

    Matches endpoints that return just the created resource ID.
    """
    albumId: str = Field(..., example="album-123")

class StandardResponse(BaseModel, Generic[T]):
    """Standardized API response envelope.

    Attributes:
        status: 'success', 'fail', or 'error'.
        message: Optional human-readable message.
        data: Optional typed payload (often a DataWrapper instance).
    """
    status: str
    message: Optional[str] = None
    data: Optional[T] = None
