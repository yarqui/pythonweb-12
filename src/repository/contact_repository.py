from __future__ import annotations

import datetime
from typing import Sequence


from sqlalchemy import select, extract, and_, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactUpdate

__all__ = ["ContactRepository"]


class ContactRepository:
    """
    A class for handling all database operations related to contacts.

    This repository abstracts the database query logic away from the service layer,
    providing a clean interface for all CRUD (Create, Read, Update, Delete)
    and custom query operations for the Contact model. All operations are scoped
    to a specific authenticated user.
    """

    def __init__(self, session: AsyncSession):
        """
        Initializes the repository with a database session.

        :param session: The SQLAlchemy asynchronous session.
        """
        self.db = session

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Retrieves a single contact by its ID for a specific user.

        :param contact_id: The ID of the contact to retrieve.
        :param user: The user who must own the contact.
        :return: The Contact object if found and owned by the user, otherwise None.
        """
        stmt = select(Contact).where(
            Contact.id == contact_id, Contact.user_id == user.id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
        Retrieves a list of contacts for a specific user with pagination and optional filtering.

        :param skip: The number of contacts to skip.
        :param limit: The maximum number of contacts to return.
        :param user: The user whose contacts are being queried.
        :param first_name: Optional filter for the contact's first name (case-insensitive).
        :param last_name: Optional filter for the contact's last name (case-insensitive).
        :param email: Optional filter for the contact's email address (case-insensitive).
        :return: A sequence of Contact objects.
        """

        stmt = select(Contact).where(Contact.user_id == user.id)
        filters = []
        if first_name:
            filters.append(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            filters.append(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            filters.append(Contact.email.ilike(f"%{email}%"))

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def get_upcoming_birthdays(self, user: User) -> Sequence[Contact]:
        """
        Retrieves contacts with birthdays in the next 7 days for a specific user.

        :param user: The user whose contacts are being queried.
        :return: A sequence of contacts with upcoming birthdays.
        """
        today = datetime.date.today()

        target_dates = [today + datetime.timedelta(days=i) for i in range(7)]
        birthday_tuples = [(d.month, d.day) for d in target_dates]

        stmt = select(Contact).where(
            and_(
                Contact.user_id == user.id,
                tuple_(
                    extract("month", Contact.birthday), extract("day", Contact.birthday)
                ).in_(birthday_tuples),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_contact(self, contact_data: dict, user: User) -> Contact:
        """
        Creates a new contact and associates it with a user.

        :param contact_data: A dictionary containing the data for the new contact.
        :param user: The user who will own the new contact.
        :return: The newly created Contact object.
        """
        contact = Contact(**contact_data, user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        """
        Partially updates an existing contact owned by a specific user.

        :param contact_id: The ID of the contact to update.
        :param body: A Pydantic schema with the fields to be updated.
        :param user: The user who must own the contact.
        :return: The updated Contact object, or None if the contact was not found.
        """

        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Deletes a contact owned by a specific user.

        :param contact_id: The ID of the contact to delete.
        :param user: The user who must own the contact.
        :return: The deleted Contact object, or None if the contact was not found.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact
