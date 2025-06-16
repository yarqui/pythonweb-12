from __future__ import annotations
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from asyncpg.exceptions import UniqueViolationError


from src.repository import ContactRepository
from src.schemas import ContactBase, ContactUpdate
from src.database.models import Contact, User

__all__ = ["ContactService"]


class ContactService:
    def __init__(self, db: AsyncSession):
        self._contact_repository = ContactRepository(session=db)

    async def get_contacts(
        self,
        skip: int,
        limit: int,
        first_name: str | None,
        last_name: str | None,
        email: str | None,
        user: User,
    ) -> Sequence[Contact]:
        contacts = await self._contact_repository.get_contacts(
            skip, limit, first_name, last_name, email, user
        )
        return contacts

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        contact = await self._contact_repository.get_contact_by_id(contact_id, user)
        return contact

    async def get_upcoming_birthdays(self, user: User) -> Sequence[Contact]:
        contacts = await self._contact_repository.get_upcoming_birthdays(user)
        return contacts

    async def create_contact(self, body: ContactBase, user: User) -> Contact:
        try:
            contact_data = body.model_dump()
            new_contact = await self._contact_repository.create_contact(
                contact_data, user
            )
            return new_contact

        # Unique constraint violation
        except IntegrityError as e:
            if isinstance(e.orig, UniqueViolationError):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Contact with email '{body.email}' already exists for this user.",
                ) from e

            # Other unexpected database errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred.",
            ) from e

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        updated_contact = await self._contact_repository.update_contact(
            contact_id, body, user
        )
        return updated_contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        deleted_contact = await self._contact_repository.delete_contact(
            contact_id, user
        )
        return deleted_contact
