"""Security utilities for password hashing and token management.

Provides functions to:
- Verify and hash passwords using bcrypt.
- Create and verify JWT access and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any]) -> str:
    """Create a short-lived JWT access token with explicit type."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"userId": str(subject), "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.ACCESS_TOKEN_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    """Create a long-lived JWT refresh token with explicit type."""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"userId": str(subject), "exp": expire, "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def _verify_token(token: str, key: str, expected_type: str) -> Optional[str]:
    """Decode and validate token type, returning userId when valid."""
    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM])
        user_id: str = payload.get("userId")
        token_type: str = payload.get("type") or payload.get("scope")
        if user_id is None or token_type != expected_type:
            return None
        return user_id
    except jwt.PyJWTError:
        return None


def verify_access_token(token: str) -> Optional[str]:
    """Verify access token, ensuring the token type is 'access'."""
    return _verify_token(token, settings.ACCESS_TOKEN_KEY, expected_type="access")


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token, ensuring the token type is 'refresh'."""
    return _verify_token(token, settings.REFRESH_TOKEN_KEY, expected_type="refresh")
