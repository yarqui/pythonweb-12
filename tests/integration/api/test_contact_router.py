import pytest
from httpx import AsyncClient
from src.database.models import User
from src.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_create_and_read_contact(authenticated_client: AsyncClient):
    """
    Tests creating a contact and then fetching it by ID to confirm creation.
    """
    create_payload = {
        "first_name": "Api",
        "last_name": "Test",
        "email": "api.test@example.com",
    }
    create_response = await authenticated_client.post(
        "/api/v1/contacts/", json=create_payload
    )
    assert create_response.status_code == 201
    created_data = create_response.json()
    contact_id = created_data["id"]

    assert created_data["first_name"] == "Api"

    get_response = await authenticated_client.get(f"/api/v1/contacts/{contact_id}")
    assert get_response.status_code == 200
    fetched_data = get_response.json()
    assert fetched_data["id"] == contact_id
    assert fetched_data["email"] == "api.test@example.com"


@pytest.mark.asyncio
async def test_get_all_contacts(authenticated_client: AsyncClient):
    """
    Tests retrieving a list of all contacts for the authenticated user.
    """
    await authenticated_client.post(
        "/api/v1/contacts/",
        json={"first_name": "Contact1", "last_name": "List", "email": "c1@test.com"},
    )

    response = await authenticated_client.get("/api/v1/contacts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["first_name"] == "Contact1"


@pytest.mark.asyncio
async def test_update_contact(authenticated_client: AsyncClient):
    """
    Tests partially updating an existing contact.
    """
    create_payload = {
        "first_name": "Original",
        "last_name": "Name",
        "email": "update@test.com",
    }
    create_response = await authenticated_client.post(
        "/api/v1/contacts/", json=create_payload
    )
    contact_id = create_response.json()["id"]

    update_payload = {"last_name": "Updated"}
    update_response = await authenticated_client.patch(
        f"/api/v1/contacts/{contact_id}", json=update_payload
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()

    assert updated_data["id"] == contact_id
    assert updated_data["first_name"] == "Original"
    assert updated_data["last_name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_contact(authenticated_client: AsyncClient):
    """
    Tests deleting a contact and ensuring it's no longer accessible.
    """
    create_payload = {
        "first_name": "ToDelete",
        "last_name": "Contact",
        "email": "delete@test.com",
    }
    create_response = await authenticated_client.post(
        "/api/v1/contacts/", json=create_payload
    )
    contact_id = create_response.json()["id"]

    delete_response = await authenticated_client.delete(
        f"/api/v1/contacts/{contact_id}"
    )
    assert delete_response.status_code == 200

    get_response = await authenticated_client.get(f"/api/v1/contacts/{contact_id}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Contact not found"


@pytest.mark.asyncio
async def test_get_contact_unauthorized(authenticated_client: AsyncClient, db_session):
    """
    Tests that a user cannot access a contact belonging to another user.
    """
    create_payload = {
        "first_name": "UserA",
        "last_name": "Contact",
        "email": "usera.contact@test.com",
    }
    create_response = await authenticated_client.post(
        "/api/v1/contacts/", json=create_payload
    )
    contact_id_for_usera = create_response.json()["id"]

    user_b = User(
        username="userB",
        email="userb@test.com",
        hashed_password=AuthService().hash_password("passwordB"),
        verified=True,
    )
    db_session.add(user_b)
    await db_session.commit()

    login_response = await authenticated_client.post(
        "/api/v1/auth/login",
        data={"username": "userb@test.com", "password": "passwordB"},
    )
    token_b = login_response.json()["access_token"]

    auth_headers_b = {"Authorization": f"Bearer {token_b}"}
    response = await authenticated_client.get(
        f"/api/v1/contacts/{contact_id_for_usera}", headers=auth_headers_b
    )

    assert response.status_code == 404
