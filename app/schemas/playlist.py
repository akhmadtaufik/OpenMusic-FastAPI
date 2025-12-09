"""Pydantic schemas for Playlist operations.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class PlaylistCreate(BaseModel):
    """Schema for creating a new playlist."""
    name: str

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
