from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.contact_service import ContactService
from src.services.user_service import UserService
from src.services.auth_service import AuthService


def get_contact_service(db: AsyncSession = Depends(get_db)) -> ContactService:
    return ContactService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_auth_service() -> AuthService:
    return AuthService()
