"""File validation utilities (magic-number based image checks).

Magic numbers are safer than Content-Type headers because clients can spoof
MIME types; inspecting the first bytes prevents accepting disguised text
files renamed as images.
"""

import re
from app.core.exceptions import ValidationError


# Magic number signatures for supported image types
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURES = [b"\xff\xd8\xff"]
GIF_SIGNATURES = [b"GIF87a", b"GIF89a"]
WEBP_SIGNATURE = b"RIFF"
WEBP_MARKER = b"WEBP"

# Extension to detected type mapping
EXTENSION_TYPE_MAP = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".gif": "gif",
    ".webp": "webp",
}


def detect_image_type(content: bytes) -> str | None:
    """Detect image type from magic numbers.
    
    Args:
        content: Raw file bytes (at least first 12 bytes needed).
        
    Returns:
        Detected type string ('png', 'jpeg', 'gif', 'webp') or None if unknown.
    """
    head = content[:12]
    
    if head.startswith(PNG_SIGNATURE):
        return "png"
    if any(head.startswith(sig) for sig in JPEG_SIGNATURES):
        return "jpeg"
    if any(head.startswith(sig) for sig in GIF_SIGNATURES):
        return "gif"
    # WebP: starts with RIFF, contains WEBP at bytes 8-12
    if head.startswith(WEBP_SIGNATURE) and WEBP_MARKER in head:
        return "webp"
    
    return None


def get_extension(filename: str) -> str:
    """Extract lowercase file extension from filename.
    
    Args:
        filename: Original filename.
        
    Returns:
        Lowercase extension including dot (e.g., '.png') or empty string.
    """
    if "." not in filename:
        return ""
    return "." + filename.rsplit(".", 1)[-1].lower()


def validate_image_bytes(filename: str, content: bytes) -> None:
    """Validate that the provided bytes represent a supported image.
    
    Performs two checks:
    1. Magic number validation - ensures file content matches image signature
    2. Extension matching - ensures file extension matches detected content type
    
    Args:
        filename: Original filename for extension checking.
        content: Raw file bytes.
        
    Raises:
        ValidationError: If the magic number does not match supported formats,
                        or if extension doesn't match the detected content type.
    """
    detected_type = detect_image_type(content)
    
    if detected_type is None:
        raise ValidationError(f"Invalid image file: {filename}. Supported formats: PNG, JPEG, GIF, WebP")
    
    # Check extension matches detected type
    extension = get_extension(filename)
    if extension:
        expected_type = EXTENSION_TYPE_MAP.get(extension)
        if expected_type and expected_type != detected_type:
            raise ValidationError(
                f"File extension mismatch: {filename}. "
                f"Extension suggests {expected_type}, but content is {detected_type}"
            )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.
    
    Removes potentially dangerous characters that could enable:
    - Path traversal attacks (../, /, \\)
    - Null byte injection
    - Special filesystem characters
    
    Args:
        filename: Original filename.
        
    Returns:
        Sanitized filename safe for storage.
    """
    if not filename:
        return "file"
    
    # Remove null bytes
    filename = filename.replace("\x00", "")
    
    # Remove path traversal attempts and directory separators
    filename = filename.replace("..", "")
    filename = filename.replace("/", "_")
    filename = filename.replace("\\", "_")
    
    # Keep only alphanumeric, dots, underscores, hyphens
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    
    # Ensure filename isn't empty after sanitization
    if not filename or filename == ".":
        return "file"
    
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:90] + ("." + ext if ext else "")
    
    return filename
