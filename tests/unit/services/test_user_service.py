from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from fastapi import HTTPException, status

from src.services.user_service import UserService
from src.schemas import UserCreate
from src.database.models import User


@pytest.fixture
def mock_repository():
    """
    Provides a MagicMock of the UserRepository where all methods that
    need to be awaited are pre-configured as AsyncMocks.
    """
    mock = MagicMock()
    mock.get_user_by_email = AsyncMock()
    mock.get_user_by_id = AsyncMock()
    mock.get_user_by_username = AsyncMock()
    mock.create_user = AsyncMock()
    mock.confirm_email = AsyncMock()
    mock.update_password = AsyncMock()
    mock.update_avatar_url = AsyncMock()
    return mock


@pytest.fixture
def mock_auth_service():
    """Mocks the AuthService and its hash_password method."""
    with patch("src.services.user_service.AuthService") as MockAuthService:
        mock_instance = MockAuthService.return_value
        mock_instance.hash_password.return_value = "hashed_password"
        yield mock_instance


@pytest.fixture
def mock_email_service():
    """Mocks the EmailService to prevent actual email sending."""
    with patch("src.services.user_service.EmailService") as MockEmailService:
        mock_instance = MockEmailService.return_value
        mock_instance.send_verification_email = AsyncMock()
        yield mock_instance


@pytest.fixture
def mock_gravatar():
    """Mocks the Gravatar service."""
    with patch("src.services.user_service.Gravatar") as MockGravatar:
        mock_instance = MockGravatar.return_value
        mock_instance.get_image.return_value = "http://mock_gravatar_url.com/avatar.jpg"
        yield mock_instance


@pytest.fixture
def user_service(mock_repository, mock_auth_service, mock_email_service, mock_gravatar):
    """
    Provides a UserService instance with all its dependencies pre-mocked.
    """
    service = UserService(db=MagicMock())
    service._repository = mock_repository
    service._auth_service = mock_auth_service
    service._email_service = mock_email_service
    return service


@pytest.mark.asyncio
async def test_create_user_success(user_service: UserService):
    """
    Tests the successful creation of a new user.
    """
    new_user_data = UserCreate(
        username="testuser", email="new@example.com", password="password123"
    )
    mock_background_tasks = MagicMock()
    mock_request = MagicMock()
    mock_request.base_url = "http://testserver/"

    user_service._repository.get_user_by_email.return_value = None
    created_user = User(
        id=1, username=new_user_data.username, email=new_user_data.email
    )
    user_service._repository.create_user.return_value = created_user

    result = await user_service.create_user(
        new_user_data, mock_background_tasks, mock_request
    )

    user_service._repository.get_user_by_email.assert_awaited_once_with(
        new_user_data.email
    )
    user_service._auth_service.hash_password.assert_called_once_with(
        new_user_data.password
    )
    user_service._repository.create_user.assert_awaited_once()
    mock_background_tasks.add_task.assert_called_once_with(
        user_service._email_service.send_verification_email,
        created_user.email,
        created_user.username,
        host=str(mock_request.base_url),
    )
    assert result.email == new_user_data.email


@pytest.mark.asyncio
async def test_create_user_already_exists(user_service: UserService):
    """
    Tests that creating a user with an existing email raises an HTTPException.
    """
    user_data = UserCreate(
        username="test", email="exists@example.com", password="password"
    )
    user_service._repository.get_user_by_email.return_value = User(
        id=1, email=user_data.email
    )

    with pytest.raises(HTTPException) as exc_info:
        await user_service.create_user(user_data, MagicMock(), MagicMock())

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "User with this email already exists."
    user_service._repository.create_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_user_by_id(user_service: UserService):
    """
    Tests that the service correctly calls the repository's get_user_by_id method.
    """
    user_id = 1
    user_service._repository.get_user_by_id.return_value = User(id=user_id)

    result = await user_service.get_user_by_id(user_id)

    user_service._repository.get_user_by_id.assert_awaited_once_with(user_id)
    assert result.id == user_id


@pytest.mark.asyncio
async def test_confirm_email(user_service: UserService):
    """
    Tests that the service correctly calls the repository's confirm_email method.
    """
    email_to_confirm = "verify@example.com"
    await user_service.confirm_email(email_to_confirm)
    user_service._repository.confirm_email.assert_awaited_once_with(email_to_confirm)


@pytest.mark.asyncio
async def test_reset_password(user_service: UserService):
    """
    Tests the password reset logic.
    """
    email = "reset@example.com"
    new_password = "new_strong_password"
    hashed_password = "hashed_new_strong_password"

    user_service._auth_service.hash_password.return_value = hashed_password

    await user_service.reset_password(email, new_password)

    user_service._auth_service.hash_password.assert_called_once_with(new_password)
    user_service._repository.update_password.assert_awaited_once_with(
        email, hashed_password
    )


@pytest.mark.asyncio
async def test_update_avatar_url(user_service: UserService):
    """
    Tests that the service correctly calls the repository's update_avatar_url method.
    """
    email = "avatar@example.com"
    new_url = "http://new-avatar.com/img.png"

    await user_service.update_avatar_url(email, new_url)

    user_service._repository.update_avatar_url.assert_awaited_once_with(email, new_url)
