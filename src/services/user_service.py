from __future__ import annotations
import logging

from fastapi import HTTPException, status, Request, BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from asyncpg.exceptions import UniqueViolationError

from libgravatar import Gravatar

from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.repository import UserRepository
from src.schemas import UserCreate
from src.database.models import User

logger = logging.getLogger(__name__)

__all__ = ["UserService"]


class UserService:
    """
    Manages the business logic for user-related operations.
    This service layer coordinates calls to the user repository and other services
    (like authentication and email) to fulfill use cases such as user creation
    and profile updates.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the service with a database session and instantiates
        its required repository and service dependencies.
        :param db: The SQLAlchemy asynchronous session.
        """
        self._repository = UserRepository(db)
        self._auth_service = AuthService()
        self._email_service = EmailService()

    async def create_user(
        self, body: UserCreate, background_tasks: BackgroundTasks, request: Request
    ) -> User:
        """
        Handles the complete business logic for registering a new user.
        This includes checking for existing users, hashing the password, generating
        an avatar, creating the user in the database, and scheduling an email
        verification to be sent in the background.
        Args:
            body (UserCreate): The Pydantic schema containing new user data.
            background_tasks (BackgroundTasks): FastAPI's background task runner.
            request (Request): The incoming request, used to get the base URL for email links.
        Raises:
            HTTPException: A 409 Conflict error if a user with the given email already exists.
        Returns:
            User: The newly created User ORM object.
        """
        existing_user = await self._repository.get_user_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )

        hashed_password = self._auth_service.hash_password(body.password)
        avatar_url = None

        try:
            g = Gravatar(body.email)
            avatar_url = g.get_image()
        except Exception as e:
            logger.warning("Could not retrieve Gravatar for %s: %s", body.email, e)

        try:
            new_user = await self._repository.create_user(
                body, hashed_password, avatar_url
            )

            background_tasks.add_task(
                self._email_service.send_verification_email,
                new_user.email,
                new_user.username,
                host=str(request.base_url),
            )

            return new_user

        except IntegrityError as e:
            # Needed for race condition
            if isinstance(e.orig, UniqueViolationError):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists (race condition).",
                ) from e
            raise

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their unique ID.
        Args:
            user_id (int): The ID of the user to retrieve.
        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self._repository.get_user_by_id(user_id)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieves a user by their unique username.
        Args:
            username (str): The username of the user to retrieve.
        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self._repository.get_user_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by their unique email address.
        Args:
            email (str): The email address of the user to retrieve.
        Returns:
            User | None: The User object if found, otherwise None.
        """
        user = await self._repository.get_user_by_email(email)
        return user

    async def confirm_email(self, email: str) -> None:
        """Pass-through to confirm a user's email in the repository."""
        await self._repository.confirm_email(email)

    async def update_avatar_url(self, email: str, url: str):
        """
        Updates the avatar URL for a specific user.

        Args:
            email (str): The email of the user whose avatar is to be updated.
            url (str): The new URL for the avatar.

        Returns:
            User | None: The updated User object if the user was found, otherwise None.
        """
        return await self._repository.update_avatar_url(email, url)
