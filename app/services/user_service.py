"""Service layer for User operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.exceptions import ValidationError

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_user(self, data: UserCreate) -> str:
        """Create a new user.
        
        Args:
            data: User creation data (username, password, fullname).
            
        Returns:
            The ID of the created user.
            
        Raises:
            ValidationError: If username is not unique.
        """
        # Check uniqueness
        stmt = select(User).where(User.username == data.username)
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValidationError(f"Username '{data.username}' already exists.")

        # Create user
        hashed_password = get_password_hash(data.password)
        new_user = User(
            username=data.username,
            password=hashed_password,
            fullname=data.fullname
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user.id
