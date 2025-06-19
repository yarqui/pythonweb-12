from __future__ import annotations
from typing import List, TYPE_CHECKING
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, func, Enum

from src.enums.roles import Role
from .base_model import IDOrmModel

if TYPE_CHECKING:
    from .contact_model import Contact


class User(IDOrmModel):
    """
    Represents a user account in the database.

    This model stores user credentials for authentication (username, email, password),
    profile information (avatar), verification status, and establishes a relationship
    to all contacts created by this user.

    Attributes:
        id (int): The primary key for the user, inherited from IDOrmModel.
        username (str): The user's unique username, used for login.
        email (str): The user's unique email address, used for login and communication.
        hashed_password (str): The user's password, securely hashed.
        avatar_url (str | None): An optional URL to the user's profile picture.
        verified (bool): A flag indicating if the user has verified their email address.
        role (Role): The role of the user, defaults to 'user'.
        created_at (datetime): The timestamp when the user account was created.
        updated_at (datetime): The timestamp when the user account was last updated.
        contacts (List[Contact]): The ORM relationship to a list of Contact objects
                                  owned by this user. The cascade option ensures that
                                  contacts are deleted when the parent user is deleted.
    """

    __tablename__ = "users"

    # User credential
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # User profile info
    avatar_url: Mapped[str | None] = mapped_column(String(255))
    verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    role: Mapped[Role] = mapped_column(
        Enum(Role, values_callable=lambda obj: [e.value for e in obj]),
        default=Role.USER,
        nullable=False,
    )

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
    contacts: Mapped[List[Contact]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}, role='{self.role.value}')>"
