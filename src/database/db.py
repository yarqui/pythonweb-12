import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False
        )

    @contextlib.asynccontextmanager
    async def session(self):
        if self._session_maker is None:
            raise ValueError("Database session manager is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()


session_manager = DatabaseSessionManager(settings.SQLALCHEMY_DATABASE_URL)


async def get_db():
    async with session_manager.session() as session:
        yield session
