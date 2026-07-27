import pytest

from src.application.exceptions import InvalidCredentialsError, UserDeactivatedError
from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserUseCase,
)
from src.infrastructure.crypto.token_manager import JwtTokenManager
from tests.unit.fakes import (
    FakePasswordHasher,
    InMemorySessionStore,
    InMemoryUserRepository,
    make_user,
)


PASSWORD = "correct-horse-battery"


def build_use_case() -> tuple[
    AuthenticateUserUseCase, InMemoryUserRepository, FakePasswordHasher, InMemorySessionStore
]:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    store = InMemorySessionStore()
    use_case = AuthenticateUserUseCase(
        user_repo=repo,
        hasher=hasher,
        token_manager=JwtTokenManager(),
        session_store=store,
    )
    return use_case, repo, hasher, store


async def test_login_success_returns_token_pair_and_registers_refresh_session() -> None:
    use_case, repo, _, store = build_use_case()
    user = make_user(password=PASSWORD)
    await repo.save(user)

    result = await use_case.execute(
        AuthenticateUserRequest(email=str(user.email), password=PASSWORD)
    )

    assert result.access_token
    assert result.refresh_token
    assert result.access_token != result.refresh_token
    assert result.token_type == "bearer"
    assert len(store.refresh_tokens) == 1
    assert list(store.refresh_tokens.values()) == [str(user.id)]


async def test_login_success_embeds_identity_claims_in_access_token() -> None:
    use_case, repo, _, _ = build_use_case()
    user = make_user(password=PASSWORD, is_superuser=True)
    await repo.save(user)

    result = await use_case.execute(
        AuthenticateUserRequest(email=str(user.email), password=PASSWORD)
    )

    claims = JwtTokenManager().decode_and_verify_token(result.access_token, expected_type="access")
    assert claims["sub"] == str(user.id)
    assert claims["is_superuser"] is True
    assert claims["username"] == user.username


async def test_login_email_lookup_is_case_insensitive() -> None:
    use_case, repo, _, _ = build_use_case()
    user = make_user(email="collector@vault.io", password=PASSWORD)
    await repo.save(user)

    result = await use_case.execute(
        AuthenticateUserRequest(email="COLLECTOR@VAULT.IO", password=PASSWORD)
    )
    assert result.access_token


async def test_login_unknown_email_raises_invalid_credentials() -> None:
    use_case, _, _, store = build_use_case()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserRequest(email="ghost@vault.io", password="whatever-pass")
        )
    assert store.refresh_tokens == {}


async def test_login_unknown_email_burns_dummy_hash_for_timing_safety() -> None:
    use_case, _, hasher, _ = build_use_case()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserRequest(email="ghost@vault.io", password="whatever-pass")
        )
    assert hasher.dummy_verification_calls == 1


async def test_login_wrong_password_raises_invalid_credentials() -> None:
    use_case, repo, _, store = build_use_case()
    user = make_user(password=PASSWORD)
    await repo.save(user)

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserRequest(email=str(user.email), password="wrong-password!")
        )
    assert store.refresh_tokens == {}


async def test_login_deactivated_account_raises_user_deactivated() -> None:
    use_case, repo, _, _ = build_use_case()
    user = make_user(password=PASSWORD, is_active=False)
    await repo.save(user)

    with pytest.raises(UserDeactivatedError):
        await use_case.execute(AuthenticateUserRequest(email=str(user.email), password=PASSWORD))


async def test_login_deactivated_account_still_requires_correct_password() -> None:
    use_case, repo, _, _ = build_use_case()
    user = make_user(password=PASSWORD, is_active=False)
    await repo.save(user)

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserRequest(email=str(user.email), password="wrong-password!")
        )


async def test_login_malformed_email_raises_domain_error() -> None:
    from src.domain.exceptions import InvalidEmailError

    use_case, _, _, _ = build_use_case()
    with pytest.raises(InvalidEmailError):
        await use_case.execute(AuthenticateUserRequest(email="not-an-email", password=PASSWORD))
