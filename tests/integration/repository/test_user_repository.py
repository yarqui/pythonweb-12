import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.user_repository import UserRepository
from src.schemas import UserCreate


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    user_data = UserCreate(
        username="newuser", email="new@example.com", password="newpassword"
    )
    hashed_password = "hashed_new_password"

    new_user = await user_repo.create_user(user_data, hashed_password)

    assert new_user.id is not None
    assert new_user.username == "newuser"
    assert new_user.email == "new@example.com"
    assert new_user.hashed_password == hashed_password
    assert not new_user.verified


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession, test_user: User):
    user_repo = UserRepository(db_session)
    found_user = await user_repo.get_user_by_email(test_user.email)

    assert found_user is not None
    assert found_user.id == test_user.id
    assert found_user.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    found_user = await user_repo.get_user_by_email("nonexistent@example.com")
    assert found_user is None


@pytest.mark.asyncio
async def test_confirm_email(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    user = User(
        username="unverified",
        email="unverified@example.com",
        hashed_password="pw",
        verified=False,
    )
    db_session.add(user)
    await db_session.commit()

    await user_repo.confirm_email("unverified@example.com")

    await db_session.refresh(user)
    assert user.verified is True


@pytest.mark.asyncio
async def test_update_password(db_session: AsyncSession, test_user: User):
    user_repo = UserRepository(db_session)
    new_password = "new_hashed_password_123"
    updated_user = await user_repo.update_password(test_user.email, new_password)

    await db_session.refresh(test_user)
    assert updated_user is not None
    assert updated_user.hashed_password == new_password
