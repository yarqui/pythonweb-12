import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError
from fastapi import HTTPException, status

from src.services.contact_service import ContactService
from src.schemas import ContactBase, ContactUpdate
from src.database.models import User, Contact


@pytest.fixture
def mock_repository():
    """
    Provides a MagicMock of the ContactRepository where all methods
    that need to be awaited are pre-configured as AsyncMocks.
    """
    mock = MagicMock()
    mock.get_contacts = AsyncMock()
    mock.get_contact_by_id = AsyncMock()
    mock.get_upcoming_birthdays = AsyncMock()
    mock.create_contact = AsyncMock()
    mock.update_contact = AsyncMock()
    mock.delete_contact = AsyncMock()
    return mock


@pytest.fixture
def contact_service(mock_repository):
    """
    Provides a ContactService instance with its repository dependency pre-mocked.
    """

    service = ContactService(db=MagicMock())
    service._contact_repository = mock_repository
    return service


@pytest.mark.asyncio
async def test_get_contacts(contact_service: ContactService):
    """
    Tests that the get_contacts service method correctly calls the repository.
    """
    mock_user = User(id=1)

    await contact_service.get_contacts(
        skip=0, limit=10, first_name="test", last_name=None, email=None, user=mock_user
    )

    contact_service._contact_repository.get_contacts.assert_awaited_once_with(
        0, 10, "test", None, None, mock_user
    )


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_service: ContactService):
    """
    Tests that the get_contact_by_id service method correctly calls the repository.
    """
    mock_user = User(id=1)
    contact_id = 99
    expected_contact = Contact(id=contact_id, user_id=mock_user.id, first_name="Test")
    contact_service._contact_repository.get_contact_by_id.return_value = (
        expected_contact
    )

    result = await contact_service.get_contact_by_id(
        contact_id=contact_id, user=mock_user
    )

    contact_service._contact_repository.get_contact_by_id.assert_awaited_once_with(
        contact_id, mock_user
    )
    assert result == expected_contact


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_service: ContactService):
    """
    Tests that the get_upcoming_birthdays service method correctly calls the repository.
    """
    mock_user = User(id=1)
    await contact_service.get_upcoming_birthdays(user=mock_user)
    contact_service._contact_repository.get_upcoming_birthdays.assert_awaited_once_with(
        mock_user
    )


@pytest.mark.asyncio
async def test_create_contact(contact_service: ContactService):
    """
    Tests the successful creation of a contact.
    """
    mock_user = User(id=1, email="test@example.com")
    contact_data = ContactBase(
        first_name="Unit", last_name="Test", email="unittest@example.com"
    )

    contact_service._contact_repository.create_contact.return_value = Contact(
        id=1, **contact_data.model_dump()
    )

    result = await contact_service.create_contact(body=contact_data, user=mock_user)

    contact_service._contact_repository.create_contact.assert_awaited_once_with(
        contact_data.model_dump(), mock_user
    )
    assert result is not None
    assert result.first_name == "Unit"


@pytest.mark.asyncio
async def test_create_contact_unique_violation(contact_service: ContactService):
    """
    Tests that create_contact correctly handles a database unique constraint violation
    by raising a 409 Conflict HTTP exception.
    """
    mock_user = User(id=1, email="test@example.com")
    contact_data = ContactBase(
        first_name="Unit", last_name="Test", email="duplicate@example.com"
    )

    integrity_error = IntegrityError("", {}, None)
    integrity_error.orig = UniqueViolationError()
    contact_service._contact_repository.create_contact.side_effect = integrity_error

    with pytest.raises(HTTPException) as exc_info:
        await contact_service.create_contact(body=contact_data, user=mock_user)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "already exists for this user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_contact(contact_service: ContactService):
    """
    Tests that the update_contact service method correctly calls the repository.
    """
    mock_user = User(id=1)
    contact_id = 99
    update_data = ContactUpdate(first_name="Updated")

    await contact_service.update_contact(
        contact_id=contact_id, body=update_data, user=mock_user
    )

    contact_service._contact_repository.update_contact.assert_awaited_once_with(
        contact_id, update_data, mock_user
    )


@pytest.mark.asyncio
async def test_delete_contact(contact_service: ContactService):
    """
    Tests that the delete_contact service method correctly calls the repository.
    """
    mock_user = User(id=1)
    contact_id = 99

    await contact_service.delete_contact(contact_id=contact_id, user=mock_user)

    contact_service._contact_repository.delete_contact.assert_awaited_once_with(
        contact_id, mock_user
    )
