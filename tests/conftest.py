from typing import AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

import asyncio
import pytest

import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.db import get_db, get_redis_client
from src.database.models import User, MinimalBase
from src.services.auth_service import AuthService
from main import app


# --- Database Fixtures ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Creates all database tables before tests run and drops them afterwards.
    This runs once per test session.
    """
    async with engine.begin() as conn:
        await conn.run_sync(MinimalBase.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(MinimalBase.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a clean database session for each test function.
    It rolls back any changes after the test is complete.
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()


# --- Redis Fixture ---
@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    """Provides a mock Redis client for each test function."""
    client = fakeredis.aioredis.FakeRedis()
    yield client
    await client.flushall()


# --- Application and Client Fixtures ---
@pytest.fixture(scope="function")
async def client(db_session, redis_client) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an AsyncClient to make requests to the FastAPI app.
    Overrides the production dependencies with test versions.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis() -> (
        AsyncGenerator[fakeredis.aioredis.FakeRedis, None]
    ):
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# --- Authentication and User Fixtures ---
@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Creates a standard, verified user in the test database."""
    auth_service = AuthService()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=auth_service.hash_password("password123"),
        verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def admin_user(db_session: AsyncSession) -> User:
    """Creates an admin user in the test database."""
    auth_service = AuthService()
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=auth_service.hash_password("adminpass"),
        verified=True,
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def access_token(test_user: User) -> str:
    """Generates an access token for the standard test user."""
    auth_service = AuthService()
    return await auth_service.create_access_token(data={"sub": test_user.email})


@pytest.fixture(scope="function")
async def authenticated_client(client: AsyncClient, access_token: str) -> AsyncClient:
    """Provides an authenticated test client with a valid Bearer token."""
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    return client


@pytest.fixture(scope="session")
def event_loop():
    """
    Creates an asyncio event loop for the entire test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_email_service(mocker):
    """Mocks the EmailService to prevent actual email sending."""
    mock = MagicMock()
    mocker.patch("src.services.user_service.EmailService", return_value=mock)
    mocker.patch("src.api.auth_router.EmailService", return_value=mock)
    mock.send_verification_email = AsyncMock()
    mock.send_password_reset_email = AsyncMock()
    return mock
