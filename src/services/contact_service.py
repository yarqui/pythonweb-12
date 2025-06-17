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
    """
    Manages the business logic for contact-related operations.

    This service layer acts as an intermediary between the API routes and the
    repository layer, enforcing business rules and coordinating data access.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the service with a database session.

        :param db: The SQLAlchemy asynchronous session.
        """
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
        """
        Retrieves or searches for a list of contacts for a specific user.

        :param skip: The number of contacts to skip for pagination.
        :param limit: The maximum number of contacts to return.
        :param user: The authenticated user to fetch contacts for.
        :param first_name: An optional filter for the contact's first name.
        :param last_name: An optional filter for the contact's last name.
        :param email: An optional filter for the contact's email address.
        :return: A list of Contact objects.
        """
        contacts = await self._contact_repository.get_contacts(
            skip, limit, first_name, last_name, email, user
        )
        return contacts

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Retrieves a single contact by its ID, ensuring it belongs to the specified user.

        :param contact_id: The ID of the contact to retrieve.
        :param user: The authenticated user who must own the contact.
        :return: The Contact object if found and owned by the user, otherwise None.
        """
        contact = await self._contact_repository.get_contact_by_id(contact_id, user)
        return contact

    async def get_upcoming_birthdays(self, user: User) -> Sequence[Contact]:
        """
        Retrieves contacts with birthdays in the next 7 days for a specific user.

        :param user: The authenticated user to fetch contacts for.
        :return: A list of contacts with upcoming birthdays.
        """
        contacts = await self._contact_repository.get_upcoming_birthdays(user)
        return contacts

    async def create_contact(self, body: ContactBase, user: User) -> Contact:
        """
        Handles the business logic for creating a new contact for a user.

        This method checks for potential duplicate emails for the given user before
        creation, raising an appropriate HTTP exception if a conflict is found.

        :param body: The Pydantic schema containing the new contact's data.
        :param user: The authenticated user who will own the new contact.
        :return: The newly created Contact object.
        :raises HTTPException: A 409 Conflict error if a contact with the same email
                               already exists for this user.
        """
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
        """
        Orchestrates the update of an existing contact.

        :param contact_id: The ID of the contact to update.
        :param body: The Pydantic schema with the fields to update.
        :param user: The authenticated user who must own the contact.
        :return: The updated Contact object, or None if not found.
        """
        updated_contact = await self._contact_repository.update_contact(
            contact_id, body, user
        )
        return updated_contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Orchestrates the deletion of an existing contact.

        :param contact_id: The ID of the contact to delete.
        :param user: The authenticated user who must own the contact.
        :return: The deleted Contact object, or None if not found.
        """
        deleted_contact = await self._contact_repository.delete_contact(
            contact_id, user
        )
        return deleted_contact
