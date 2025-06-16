from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Query

from src.schemas import ContactUpdate, ContactBase, ContactResponse
from src.services import ContactService, get_contact_service, get_current_user
from src.database.models import User

contact_router = APIRouter(prefix="/contacts", tags=["contacts"])


@contact_router.get(
    "/", response_model=List[ContactResponse], summary="Get all contacts"
)
async def get_contacts(
    current_user: User = Depends(get_current_user),
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    skip: int = 0,
    limit: int = Query(default=10, ge=1, le=100),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Retrieves a list of contacts for the current user.
    Can be filtered by first name, last name, or email.
    """
    contacts = await contact_service.get_contacts(
        skip, limit, first_name, last_name, email, current_user
    )
    return contacts


@contact_router.get(
    "/birthdays",
    response_model=List[ContactResponse],
    summary="Get upcoming birthdays",
)
async def get_upcoming_birthdays(
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Retrieves contacts with birthdays in the next 7 days for the current user."""
    contacts = await contact_service.get_upcoming_birthdays(current_user)
    return contacts


@contact_router.get(
    "/{contact_id}", response_model=ContactResponse, summary="Get contact by ID"
)
async def get_contact_by_id(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Retrieves a single contact by ID, if it belongs to the current user."""
    contact = await contact_service.get_contact_by_id(contact_id, current_user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@contact_router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contact",
)
async def create_contact(
    body: ContactBase,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """
    Creates a new contact for the current authenticated user.
    """
    new_contact = await contact_service.create_contact(body, current_user)
    return new_contact


@contact_router.patch(
    "/{contact_id}", response_model=ContactResponse, summary="Update contact"
)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Updates an existing contact if it belongs to the current authenticated user."""
    contact = await contact_service.update_contact(contact_id, body, current_user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@contact_router.delete("/{contact_id}", response_model=ContactResponse)
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    contact_service: ContactService = Depends(get_contact_service),
):
    """Deletes a contact if it belongs to the current authenticated user."""
    contact = await contact_service.delete_contact(contact_id, current_user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact
