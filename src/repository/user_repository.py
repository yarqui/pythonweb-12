from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from src.database.models import User
from src.schemas import UserCreate

__all__ = ["UserRepository"]


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def _get_user_by_attribute(
        self, attr: InstrumentedAttribute, value: str | int
    ) -> User | None:
        """
        A generic private method to get a user by a specific attribute.
        :param attr: The SQLAlchemy model attribute to filter by (e.g., User.id, User.email).
        :param value: The value to match.
        :return: A User object or None.
        """
        stmt = select(User).where(attr == value)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self._get_user_by_attribute(User.id, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self._get_user_by_attribute(User.email, email)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self._get_user_by_attribute(User.username, username)

    async def create_user(
        self, body: UserCreate, hashed_password: str, avatar_url: str | None = None
    ) -> User:
        new_user = User(
            username=body.username,
            email=body.email,
            hashed_password=hashed_password,
            avatar_url=avatar_url,
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def confirm_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)
        if user:
            user.verified = True
            await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User | None:
        user = await self.get_user_by_email(email)
        if user:
            user.avatar_url = url
            await self.db.commit()
            await self.db.refresh(user)
            return user
