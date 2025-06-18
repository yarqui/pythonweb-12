from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base schema for a user, containing shared fields."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Inherits from UserBase and adds the password field, which is required only during creation.
    """

    password: str = Field(min_length=6, max_length=128)


class UserResponse(UserBase):
    """
    Schema for the data returned by the API when fetching a user.
    Excludes sensitive information like the password.
    """

    id: int

    avatar_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestEmail(BaseModel):
    """Schema for the /request_email endpoint body."""

    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Schema for the initial password reset request."""

    email: EmailStr


class ResetPasswordForm(BaseModel):
    """Schema for the final password reset confirmation."""

    token: str
    new_password: str = Field(min_length=6, max_length=128)
