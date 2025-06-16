from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class ContactBase(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=20)
    birthday: date | None = None


class ContactUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=50)
    last_name: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    birthday: date | None = None


class ContactResponse(ContactBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
