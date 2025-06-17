"""
This module defines the foundational components for the SQLAlchemy ORM,
including a shared MetaData object and base model classes.
"""

from sqlalchemy import MetaData, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


metadata_obj = MetaData()


class MinimalBase(DeclarativeBase):
    """A minimal declarative base class for all ORM models.

    This class provides the shared MetaData object to all models that inherit from it,
    ensuring they are all part of the same schema registry. It is marked as abstract
    so that SQLAlchemy does not try to create a table for it.
    """

    __abstract__ = True
    metadata = metadata_obj


class IDOrmModel(MinimalBase):
    """An abstract base model that provides a reusable integer primary key column.

    Models that need an 'id' primary key can inherit from this class to avoid
    redefining the same column in every model.
    """

    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
