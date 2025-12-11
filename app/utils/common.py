"""Shared utility helpers for IDs, dates, and string sanitization."""

import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Return a UUID4 string."""
    return str(uuid.uuid4())


def isoformat(dt: datetime) -> str:
    """Return an ISO 8601 string with UTC offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def clean_string(value: str, max_length: int | None = None) -> str:
    """Strip whitespace and optionally truncate to max_length."""
    cleaned = value.strip()
    if max_length is not None:
        cleaned = cleaned[:max_length]
    return cleaned
