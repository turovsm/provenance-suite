import pytest

from src.application.exceptions import UserAlreadyExistsError
from src.application.use_cases.register_user import RegisterUserRequest, RegisterUserUseCase
from src.domain.exceptions import InvalidEmailError
from tests.unit.fakes import FakePasswordHasher, InMemoryUserRepository, make_user


def build_use_case() -> tuple[RegisterUserUseCase, InMemoryUserRepository, FakePasswordHasher]:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    return RegisterUserUseCase(user_repo=repo, hasher=hasher), repo, hasher


async def test_register_success_persists_user_with_defaults() -> None:
    use_case, repo, _ = build_use_case()

    result = await use_case.execute(
        RegisterUserRequest(
            username="new_collector", email="new@vault.io", password="a-strong-password"
        )
    )

    stored = await repo.find_by_id(result.id)
    assert stored is not None
    assert stored.username == "new_collector"
    assert str(stored.email) == "new@vault.io"
    assert stored.is_active is True
    assert stored.is_superuser is False


async def test_register_stores_hash_never_plaintext() -> None:
    use_case, repo, hasher = build_use_case()
    password = "a-strong-password"

    result = await use_case.execute(
        RegisterUserRequest(username="new_collector", email="new@vault.io", password=password)
    )

    stored = await repo.find_by_id(result.id)
    assert stored is not None
    assert stored.hashed_password == hasher.hash_password(password)
    assert stored.hashed_password != password


async def test_register_normalizes_email_to_lowercase() -> None:
    use_case, repo, _ = build_use_case()

    result = await use_case.execute(
        RegisterUserRequest(username="x", email="MiXeD@Vault.IO", password="a-strong-password")
    )
    stored = await repo.find_by_id(result.id)
    assert stored is not None
    assert str(stored.email) == "mixed@vault.io"


async def test_register_duplicate_username_conflicts() -> None:
    use_case, repo, _ = build_use_case()
    await repo.save(make_user(username="taken", email="first@vault.io"))

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserRequest(username="taken", email="other@vault.io", password="p" * 12)
        )


async def test_register_duplicate_email_conflicts_case_insensitively() -> None:
    use_case, repo, _ = build_use_case()
    await repo.save(make_user(username="first", email="dup@vault.io"))

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserRequest(username="second", email="DUP@vault.io", password="p" * 12)
        )


@pytest.mark.parametrize(
    "bad_email",
    ["", "plainaddress", "@no-local.io", "user@", "user@domain", "user @vault.io"],
)
async def test_register_invalid_email_raises(bad_email: str) -> None:
    use_case, _, _ = build_use_case()

    with pytest.raises(InvalidEmailError):
        await use_case.execute(
            RegisterUserRequest(username="x", email=bad_email, password="p" * 12)
        )
