import pytest
from httpx import AsyncClient
from io import BytesIO

from src.database.models import User
from src.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_get_own_profile(authenticated_client: AsyncClient, test_user: User):
    """
    Tests successfully retrieving the profile for the currently authenticated user.
    """
    response = await authenticated_client.get("/api/v1/users/me")

    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == test_user.email
    assert profile_data["username"] == test_user.username
    assert profile_data["id"] == test_user.id


@pytest.mark.asyncio
async def test_update_avatar_forbidden_for_user(authenticated_client: AsyncClient):
    """
    Tests that a regular user (without admin role) receives a 403 Forbidden error
    when trying to access an admin-only route like updating an avatar.
    """
    dummy_file = BytesIO(b"dummy image data")

    response = await authenticated_client.patch(
        "/api/v1/users/avatar", files={"file": ("test.jpg", dummy_file, "image/jpeg")}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions"


@pytest.mark.asyncio
async def test_update_avatar_success_for_admin(
    client: AsyncClient, admin_user: User, mocker
):
    """
    Tests that an admin user can successfully update their avatar.
    This test relies on an 'admin_user' fixture being available in conftest.py.
    """
    mocker.patch(
        "src.api.user_router.upload_file", return_value="http://new.avatar/url.jpg"
    )

    auth_service = AuthService()
    admin_token = await auth_service.create_access_token(data={"sub": admin_user.email})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    dummy_file = BytesIO(b"dummy admin image data")
    response = await client.patch(
        "/api/v1/users/avatar",
        files={"file": ("admin_avatar.png", dummy_file, "image/png")},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == admin_user.email
    assert data["avatar_url"] == "http://new.avatar/url.jpg"
