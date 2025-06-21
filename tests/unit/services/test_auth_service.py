import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import pickle
from datetime import timedelta

from jose import jwt
from fastapi import HTTPException, status

from src.services.auth_service import AuthService, get_current_user, RoleAccessService
from src.database.models import User
from src.enums.roles import Role
from src.conf import config


@pytest.fixture
def mock_user_repo():
    """Provides a fresh mock of the UserRepository for each test."""
    mock = MagicMock()
    mock.get_user_by_email = AsyncMock()
    mock.get_user_by_username = AsyncMock()
    return mock


@pytest.fixture
def mock_redis_client():
    """Provides a mock Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.expire = AsyncMock()
    return mock


@pytest.fixture
def auth_service():
    """Provides an instance of AuthService for testing."""
    return AuthService()


def test_verify_password(auth_service: AuthService):
    """Tests password hashing and verification logic."""
    password = "strong_password"
    hashed_password = auth_service.hash_password(password)

    assert auth_service.verify_password(password, hashed_password) is True
    assert auth_service.verify_password("wrong_password", hashed_password) is False


@pytest.mark.asyncio
async def test_create_access_token_with_custom_expiry(auth_service: AuthService):
    """Tests creating an access token with a custom expiry delta."""
    custom_delta = timedelta(minutes=5)
    token = await auth_service.create_access_token(
        data={"sub": "user@test.com"}, expires_delta=custom_delta
    )
    payload = jwt.decode(
        token,
        config.get_settings().JWT_SECRET_KEY,
        algorithms=[config.get_settings().JWT_ALGORITHM],
    )

    assert (payload["exp"] - payload["iat"]) == pytest.approx(
        custom_delta.total_seconds(), abs=1
    )


@pytest.mark.asyncio
async def test_decode_refresh_token(auth_service: AuthService):
    """Tests successful decoding of a valid refresh token."""
    email = "refresh@test.com"
    token = await auth_service.create_refresh_token(data={"sub": email})
    decoded_email = await auth_service.decode_refresh_token(token)
    assert decoded_email == email


@pytest.mark.asyncio
async def test_decode_refresh_token_invalid_scope(auth_service: AuthService):
    """Tests that a token with the wrong scope fails decoding."""
    access_token = await auth_service.create_access_token(data={"sub": "user@test.com"})
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.decode_refresh_token(access_token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid scope for token"


@pytest.mark.asyncio
async def test_decode_password_reset_token(auth_service: AuthService):
    """Tests successful decoding of a password reset token."""
    email = "pwreset@test.com"
    token = auth_service.create_password_reset_token(data={"sub": email})
    decoded_email = await auth_service.decode_password_reset_token(token)
    assert decoded_email == email


@pytest.mark.asyncio
async def test_login_user_by_username(
    auth_service: AuthService, mock_user_repo, mock_redis_client
):
    """Tests successful user login using a username instead of an email."""
    mock_db = MagicMock()
    password = "password123"
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password=auth_service.hash_password(password),
        verified=True,
    )
    mock_user_repo.get_user_by_username.return_value = user

    with patch("src.services.auth_service.UserRepository", return_value=mock_user_repo):
        mock_form = MagicMock()
        mock_form.username = "testuser"  # Using username here
        mock_form.password = password

        result = await auth_service.login_user(mock_form, mock_db, mock_redis_client)

        assert "access_token" in result
        mock_user_repo.get_user_by_username.assert_awaited_once_with("testuser")
        mock_redis_client.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_current_user_from_cache(
    auth_service: AuthService, mock_redis_client
):
    """Tests that get_current_user successfully retrieves a user from the cache."""
    user = User(id=1, email="cached@user.com", role=Role.USER)
    mock_redis_client.get.return_value = pickle.dumps(user)

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    mock_db = MagicMock()

    result_user = await get_current_user(
        request=MagicMock(),
        token=access_token,
        db=mock_db,
        redis_client=mock_redis_client,
    )

    mock_redis_client.get.assert_awaited_once_with(f"user:{user.email}")
    assert result_user.email == user.email
    mock_db.assert_not_called()


@pytest.mark.asyncio
async def test_get_current_user_jwt_error(auth_service: AuthService):
    """Tests that get_current_user raises an exception for a malformed token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=MagicMock(),
            token="not_a_real_token",
            db=MagicMock(),
            redis_client=MagicMock(),
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_not_in_db(
    auth_service: AuthService, mock_user_repo, mock_redis_client
):
    """Tests that get_current_user raises an exception if the user from a valid token is not in the database."""
    email = "ghost@user.com"
    access_token = await auth_service.create_access_token(data={"sub": email})

    mock_redis_client.get.return_value = None
    mock_user_repo.get_user_by_email.return_value = None

    with patch("src.services.auth_service.UserRepository", return_value=mock_user_repo):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(
                request=MagicMock(),
                token=access_token,
                db=MagicMock(),
                redis_client=mock_redis_client,
            )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_role_access_service_success():
    """Tests that RoleAccessService allows access for a user with a permitted role."""
    admin_user = User(role=Role.ADMIN)
    is_admin_service = RoleAccessService(allowed_roles=[Role.ADMIN])
    result_user = await is_admin_service(current_user=admin_user)
    assert result_user == admin_user


@pytest.mark.asyncio
async def test_role_access_service_forbidden():
    """Tests that RoleAccessService denies access for a user with a disallowed role."""
    user = User(role=Role.USER)
    is_admin_service = RoleAccessService(allowed_roles=[Role.ADMIN])
    with pytest.raises(HTTPException) as exc_info:
        await is_admin_service(current_user=user)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
