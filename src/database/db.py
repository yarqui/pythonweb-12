import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.conf.config import settings


class DatabaseSessionManager:
    """Manages the database engine and session creation."""

    def __init__(self, url: str):
        """
        Initializes the database engine and session factory.

        :param url: The database connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Provides a transactional scope around a series of operations.

        This async context manager creates a new session, yields it for use in a
        'with' block, and guarantees that the session is rolled back on any database
        error and closed upon exit.
        """
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
    """
    FastAPI dependency that provides a database session for a single request.

    Uses the session_manager context manager to ensure that the session is
    properly opened, closed, and rolled back in case of an error.
    """
    async with session_manager.session() as session:
        yield session
