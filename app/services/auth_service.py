"""Service layer for Authentication operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.user import User
from app.models.authentication import Authentication
from app.schemas.auth import LoginPayload, AuthToken
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_refresh_token
from app.core.exceptions import AuthenticationError, ValidationError

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, data: LoginPayload) -> AuthToken:
        """Authenticate a user and return tokens.
        
        Args:
            data: Login credentials.
            
        Returns:
            AuthToken containing access and refresh tokens.
            
        Raises:
            AuthenticationError: If credentials are invalid.
        """
        # Find user
        stmt = select(User).where(User.username == data.username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(data.password, user.password):
            raise AuthenticationError("Invalid username or password")
            
        # Generate tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        # Store refresh token
        auth_entry = Authentication(token=refresh_token)
        self.db.add(auth_entry)
        await self.db.commit()
        
        return AuthToken(accessToken=access_token, refreshToken=refresh_token)

    async def refresh_token(self, token: str) -> AuthToken:
        """Refresh tokens using a valid refresh token (with token rotation).
        
        Implements secure token rotation:
        1. Verify old refresh token exists in DB
        2. Delete old refresh token immediately (prevents reuse)
        3. Verify token signature/claims
        4. Generate new access AND refresh tokens
        5. Save new refresh token to DB
        
        Args:
            token: The refresh token string.
            
        Returns:
            AuthToken with new access and refresh tokens.
            
        Raises:
            AuthenticationError: If token is missing from DB or invalid.
        """
        # Check DB existence
        stmt = select(Authentication).where(Authentication.token == token)
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if not stored_token:
            raise ValidationError("Refresh token not found in database")
        
        # Delete old token immediately (token rotation - prevents reuse)
        await self.db.delete(stored_token)
        await self.db.commit()
            
        # Verify signature/claims
        user_id = verify_refresh_token(token)
        if not user_id:
            raise AuthenticationError("Invalid refresh token signature")

        # Generate new tokens (both access and refresh)
        new_access_token = create_access_token(subject=user_id)
        new_refresh_token = create_refresh_token(subject=user_id)
        
        # Store new refresh token
        new_auth_entry = Authentication(token=new_refresh_token)
        self.db.add(new_auth_entry)
        await self.db.commit()

        return AuthToken(accessToken=new_access_token, refreshToken=new_refresh_token)

    async def logout(self, token: str) -> None:
        """Revoke a refresh token.
        
        Args:
            token: The refresh token to revoke.
        """
        # Check DB existence (optional strictness, but good for idempotency)
        # We'll just try to delete it.
        stmt = select(Authentication).where(Authentication.token == token)
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()
        
        if stored_token:
            await self.db.delete(stored_token)
            await self.db.commit()
        else:
            raise ValidationError("Refresh token not found in database")
