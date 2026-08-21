import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_user_repository_crud_lifecycle(db_session: AsyncSession) -> None:
    repo = SqlAlchemyUserRepository(db_session)
    user_id = uuid.uuid4()

    user = User(
        id=user_id,
        username="vault_admin",
        email=EmailAddress("admin@vault.io"),
        hashed_password="hashed-argon2-string",
        role=UserRole.ADMIN,
        is_active=True,
    )

    await repo.save(user)
    await db_session.flush()

    found_id = await repo.find_by_id(user_id)
    assert found_id is not None
    assert found_id.username == "vault_admin"
    assert str(found_id.email) == "admin@vault.io"
    assert found_id.role == UserRole.ADMIN

    found_email = await repo.find_by_email(EmailAddress("admin@vault.io"))
    assert found_email is not None
    assert found_email.id == user_id

    found_username = await repo.find_by_username("vault_admin")
    assert found_username is not None
    assert found_username.id == user_id

    user.username = "trusted_member"
    user.role = UserRole.TRUSTED
    user.deactivate()
    await repo.save(user)
    await db_session.flush()

    updated = await repo.find_by_id(user_id)
    assert updated is not None
    assert updated.username == "trusted_member"
    assert updated.role == UserRole.TRUSTED
    assert updated.is_active is False

    assert await repo.find_by_id(uuid.uuid4()) is None
    assert await repo.find_by_username("non_existent") is None
