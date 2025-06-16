from __future__ import annotations

import datetime
from typing import Sequence


from sqlalchemy import select, extract, and_, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactUpdate

__all__ = ["ContactRepository"]


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
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
        contact = Contact(**contact_data, user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:

        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            update_data = body.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(contact, key, value)

            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact
