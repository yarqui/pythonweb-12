from __future__ import annotations
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import IDOrmModel

if TYPE_CHECKING:
    from .user_model import User


class Contact(IDOrmModel):
    """
    Represents a contact record in the database.

    Each contact is associated with a specific user and contains personal
    information such as name, email, phone number, and birthday. The email
    is unique per user.

    Attributes:
        id (int): The primary key for the contact, inherited from IDOrmModel.
        user_id (int): The foreign key linking to the owner user in the 'users' table.
        first_name (str): The contact's first name.
        last_name (str): The contact's last name.
        email (str | None): The contact's email address. Must be unique for a given user.
        phone_number (str | None): The contact's phone number.
        birthday (date | None): The contact's date of birth.
        created_at (datetime): The timestamp when the contact was created.
        updated_at (datetime): The timestamp when the contact was last updated.
        user (User): The ORM relationship to the parent User object.
    """
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("user_id", "email", name="unique_contact_user_email"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Contact info
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(60))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    birthday: Mapped[date | None] = mapped_column(Date)

    #  Timestamps
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', email='{self.email}', phone_number='{self.phone_number}', birthday='{self.birthday}', user_id='{self.user_id}')>"
