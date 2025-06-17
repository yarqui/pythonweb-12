from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.contact_service import ContactService
from src.services.user_service import UserService
from src.services.auth_service import AuthService


def get_contact_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    """
    FastAPI dependency to get an instance of ContactService.

    Creates a new ContactService with a database session provided by the
    get_db dependency for each incoming request.

    :param db: The asynchronous database session.
    :return: An instance of ContactService.
    """
    return ContactService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    FastAPI dependency to get an instance of UserService.

    Creates a new UserService with a database session provided by the
    get_db dependency for each incoming request.

    :param db: The asynchronous database session.
    :return: An instance of UserService.
    """
    return UserService(db)


def get_auth_service() -> AuthService:
    """
    FastAPI dependency to get an instance of AuthService.

    Since AuthService is stateless, a new instance is created for each request
    that depends on it.

    :return: An instance of AuthService.
    """
    return AuthService()
