import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Contact
from src.repository.contact_repository import ContactRepository
from src.schemas import ContactUpdate


@pytest.mark.asyncio
async def test_create_contact(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)

    contact_repo = ContactRepository(db_session)
    contact_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
    }
    new_contact = await contact_repo.create_contact(contact_data, live_user)

    assert new_contact.id is not None
    assert new_contact.first_name == "Jane"
    assert new_contact.user_id == live_user.id


@pytest.mark.asyncio
async def test_get_contact_by_id(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user_id=live_user.id,
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    contact_repo = ContactRepository(db_session)
    found_contact = await contact_repo.get_contact_by_id(contact.id, live_user)

    assert found_contact is not None
    assert found_contact.id == contact.id


@pytest.mark.asyncio
async def test_get_contact_by_id_wrong_user(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user_id=live_user.id,
    )
    db_session.add(contact)

    other_user = User(
        username="otheruser", email="other@example.com", hashed_password="pw"
    )
    db_session.add(other_user)
    await db_session.commit()

    contact_repo = ContactRepository(db_session)
    found_contact = await contact_repo.get_contact_by_id(contact.id, other_user)

    assert found_contact is None


@pytest.mark.asyncio
async def test_get_contacts_filtered(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user_id=live_user.id,
    )
    db_session.add(contact)
    await db_session.commit()

    contact_repo = ContactRepository(db_session)
    contacts = await contact_repo.get_contacts(0, 10, "John", None, None, live_user)

    assert len(contacts) == 1
    assert contacts[0].first_name == "John"


@pytest.mark.asyncio
async def test_update_contact(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user_id=live_user.id,
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    contact_repo = ContactRepository(db_session)
    update_data = ContactUpdate(last_name="Smith", email="john.smith@example.com")

    updated_contact = await contact_repo.update_contact(
        contact.id, update_data, live_user
    )

    assert updated_contact is not None
    assert updated_contact.last_name == "Smith"
    assert updated_contact.email == "john.smith@example.com"


@pytest.mark.asyncio
async def test_delete_contact(db_session: AsyncSession, test_user: User):
    live_user = await db_session.merge(test_user)
    contact = Contact(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        user_id=live_user.id,
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    contact_repo = ContactRepository(db_session)
    deleted_contact = await contact_repo.delete_contact(contact.id, live_user)

    assert deleted_contact is not None

    found_contact = await contact_repo.get_contact_by_id(contact.id, live_user)
    assert found_contact is None
