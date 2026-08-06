from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    User specific repository.
    Defines query interfaces specific to User profiles.
    """
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetches a user profile by unique email address."""
        result = await self.db.execute(
            select(self.model)
            .options(selectinload(self.model.roles))
            .filter(self.model.email == email)
        )
        return result.scalars().first()
