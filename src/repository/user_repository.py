from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from src.database.models import User
from src.schemas import UserCreate

__all__ = ["UserRepository"]


class UserRepository:
    """
    A class for handling all database operations related to users.

    This repository abstracts the database query logic away from the service layer,
    providing a clean interface for all CRUD (Create, Read, Update, Delete)
    and custom query operations for the User model.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the repository with a database session.

        Args:
            session: The SQLAlchemy asynchronous session.
        """
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
        """
        Retrieves a single user by their unique ID.

        :param user_id: The ID of the user to retrieve.
        :return: The User object if found, otherwise None.
        """
        return await self._get_user_by_attribute(User.id, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieves a single user by their unique email address.

        :param email: The email address of the user to retrieve.
        :return: The User object if found, otherwise None.
        """
        return await self._get_user_by_attribute(User.email, email)

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieves a single user by their unique username.

        :param username: The username of the user to retrieve.
        :return: The User object if found, otherwise None.
        """
        return await self._get_user_by_attribute(User.username, username)

    async def create_user(
        self, body: UserCreate, hashed_password: str, avatar_url: str | None = None
    ) -> User:
        """
        Creates a new user record in the database.

        :param body: A Pydantic schema containing the username and email.
        :param hashed_password: The securely hashed password for the new user.
        :param avatar_url: An optional URL for the user's avatar.
        :return: The newly created User object.
        """
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
        """
        Sets the 'verified' flag to True for a user with the given email.

        If no user is found with the specified email, the method does nothing.

        Args:
            email (str): The email of the user to verify.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.verified = True
            await self.db.commit()

    async def update_password(
        self, email: str, new_hashed_password: str
    ) -> User | None:
        """
        Updates the password for a user identified by their email.

        Args:
            email (str): The email of the user to update.
            new_hashed_password (str): The new, already-hashed password.

        Returns:
            User | None: The updated User object if found, otherwise None.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.hashed_password = new_hashed_password
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_avatar_url(self, email: str, url: str) -> User | None:
        """
        Updates the avatar URL for a specific user.

        :param email: The email of the user to update.
        :param url: The new URL for the avatar.
        :return: The updated User object if the user was found, otherwise None.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.avatar_url = url
            await self.db.commit()
            await self.db.refresh(user)
            return user
