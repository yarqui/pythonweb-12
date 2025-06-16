from sqlalchemy import MetaData, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


metadata_obj = MetaData()


class MinimalBase(DeclarativeBase):
    __abstract__ = True
    metadata = metadata_obj


class IDOrmModel(MinimalBase):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
