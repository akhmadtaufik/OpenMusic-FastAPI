"""File validation utilities (magic-number based image checks)."""

from app.core.exceptions import ValidationError


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURES = [b"\xff\xd8\xff"]


def validate_image_bytes(filename: str, content: bytes) -> None:
    """Validate that the provided bytes represent a supported image.

    Raises ValidationError if the magic number does not match PNG or JPEG.
    """
    head = content[:8]
    if head.startswith(PNG_SIGNATURE):
        return
    if any(head.startswith(sig) for sig in JPEG_SIGNATURES):
        return
    raise ValidationError(f"Invalid image file: {filename}")
