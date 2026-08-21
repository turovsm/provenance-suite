import uuid

import pytest

from src.domain.entities.user import User
from src.domain.exceptions import DomainInvariantError
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole


def make_user(**overrides) -> User:
    defaults = dict(
        id=uuid.uuid4(),
        username="collector",
        email=EmailAddress("collector@vault.io"),
        hashed_password="hash",
        role=UserRole.USER,
    )
    defaults.update(overrides)
    return User(**defaults)


def test_create_new_defaults_to_active_user_role() -> None:
    user = User.create_new(
        username="  padded  ", email=EmailAddress("u@vault.io"), hashed_password="h"
    )
    assert user.is_active is True
    assert user.role == UserRole.USER
    assert user.is_admin is False
    assert user.username == "padded"
    assert isinstance(user.id, uuid.UUID)


def test_create_new_with_admin_role() -> None:
    admin = User.create_new(
        username="admin",
        email=EmailAddress("admin@vault.io"),
        hashed_password="h",
        role=UserRole.ADMIN,
    )
    assert admin.role == UserRole.ADMIN
    assert admin.is_admin is True


def test_create_new_generates_unique_ids() -> None:
    a = User.create_new(username="a", email=EmailAddress("a@vault.io"), hashed_password="h")
    b = User.create_new(username="b", email=EmailAddress("b@vault.io"), hashed_password="h")
    assert a.id != b.id


def test_deactivate_regular_user() -> None:
    user = make_user(role=UserRole.USER)
    user.deactivate()
    assert user.is_active is False


def test_deactivate_admin_violates_invariant() -> None:
    admin = make_user(role=UserRole.ADMIN)
    with pytest.raises(DomainInvariantError):
        admin.deactivate()
    assert admin.is_active is True


def test_activate_restores_access() -> None:
    user = make_user(is_active=False)
    user.activate()
    assert user.is_active is True
