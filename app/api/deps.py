"""Common FastAPI dependencies for the API layer.

Currently exposes an async database session provider used by route handlers.
Sessions are opened and closed per-request using the project-wide session
factory.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async SQLAlchemy session.

    This function is intended for FastAPI dependency injection. It opens an
    async session from the global factory and ensures proper cleanup once the
    request is finished.

    Yields:
        AsyncSession: The active database session for the request.
    """
    async with AsyncSessionLocal() as session:
        yield session

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import verify_refresh_token, verify_password # Not quite correct, we need access token vertification
from app.core.config import settings
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="authentications")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Validate access token and return user ID."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.ACCESS_TOKEN_KEY, algorithms=["HS256"])
        user_id: str = payload.get("userId")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    return user_id
