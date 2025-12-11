"""Pydantic schemas for Playlist operations.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional

class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Playlist name must not be empty")
        if len(v) > 100:
            raise ValueError("Playlist name must be at most 100 characters")
        return v

class PlaylistResponse(BaseModel):
    """Schema for returning playlist details."""
    id: str
    name: str
    username: str

    model_config = ConfigDict(from_attributes=True)

class PlaylistSongRequest(BaseModel):
    """Schema for adding a song to a playlist."""
    songId: str

class SongInPlaylist(BaseModel):
    """Schema for song details within a playlist response."""
    id: str
    title: str
    performer: str

    model_config = ConfigDict(from_attributes=True)

class PlaylistWithSongs(BaseModel):
    """Schema for playlist details including songs."""
    id: str
    name: str
    username: str
    songs: List[SongInPlaylist] = []

    model_config = ConfigDict(from_attributes=True)

class PlaylistWithSongsResponse(BaseModel):
    """Wrapper response for playlist with songs."""
    status: str = "success"
    data: dict 
