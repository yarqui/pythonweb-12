import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from src.database.models import User
from src.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, mocker):
    """
    Tests successful user registration via the /signup endpoint.
    """
    mocker.patch(
        "src.services.user_service.EmailService.send_verification_email",
        new_callable=AsyncMock,
    )

    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "integ_user",
            "email": "integ@test.com",
            "password": "a_strong_password_123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "integ@test.com"
    assert data["username"] == "integ_user"
    assert "id" in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_signup_conflict(client: AsyncClient, test_user: User):
    """
    Tests that signing up with an email that already exists returns a 409 Conflict error.
    """
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "anotheruser",
            "email": test_user.email,
            "password": "password123",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_and_get_profile(client: AsyncClient, test_user: User):
    """
    Tests successful login and subsequent profile retrieval.
    This verifies the full authentication and authorization cycle.
    """
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "password123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    auth_headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = await client.get("/api/v1/users/me", headers=auth_headers)

    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["email"] == test_user.email
    assert profile_data["username"] == test_user.username


@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient, test_user: User):
    """
    Tests that login fails with incorrect credentials.
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "wrong_password_!@#$"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_email_verification_flow(client: AsyncClient, db_session, mocker):
    """
    Tests the full email verification flow.
    """
    unverified_user_data = {
        "username": "unverified",
        "email": "unverified@test.com",
        "password": "password123",
    }
    mocker.patch(
        "src.services.user_service.EmailService.send_verification_email",
        new_callable=AsyncMock,
    )
    signup_response = await client.post(
        "/api/v1/auth/signup", json=unverified_user_data
    )
    assert signup_response.status_code == 201

    auth_service = AuthService()
    verification_token = auth_service.create_email_token(
        {"sub": unverified_user_data["email"]}
    )

    response = await client.get(f"/api/v1/auth/verified_email/{verification_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email confirmed successfully."

    user_in_db = await db_session.get(User, signup_response.json()["id"])
    assert user_in_db is not None
    assert user_in_db.verified is True

    response = await client.get(f"/api/v1/auth/verified_email/{verification_token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Your email is already verified."
