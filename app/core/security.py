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
    """Create a short-lived JWT access token.
    
    Payload MUST contain 'userId'.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"userId": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.ACCESS_TOKEN_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    """Create a long-lived JWT refresh token.
    
    The refresh token itself is just a JWT, but we will store it in the DB 
    to manage logout (revocation).
    """
    # Refresh tokens can last longer, e.g., 7 days. 
    # For this task, we'll just set it to a reasonably long time or matching expiration if simpler.
    # Let's say 7 days for now as is standard.
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"userId": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> Optional[str]:
    """Verify a refresh token and return the userId (subject) if valid."""
    try:
        payload = jwt.decode(token, settings.REFRESH_TOKEN_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("userId")
        if user_id is None:
            return None
        return user_id
    except jwt.PyJWTError:
        return None
