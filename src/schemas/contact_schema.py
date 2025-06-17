from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class ContactBase(BaseModel):
    """Base schema for a contact, containing all fields a user can input."""

    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=20)
    birthday: date | None = None


class ContactUpdate(BaseModel):
    """
    Schema for partially updating an existing contact.
    All fields are optional, allowing the client to send only the data they wish to change.
    """

    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    birthday: date | None = None


class ContactResponse(ContactBase):
    """
    Schema for the data returned by the API when fetching a contact.
    Includes database-generated fields like id and timestamps.
    """

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
