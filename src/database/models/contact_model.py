from __future__ import annotations
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Date, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import IDOrmModel

if TYPE_CHECKING:
    from .user_model import User


class Contact(IDOrmModel):
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
