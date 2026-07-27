import pytest

from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserUseCase,
    LogoutUseCase,
    RefreshTokenRequest,
    RefreshTokenUseCase,
    TokenPairResponse,
)
from src.infrastructure.crypto.token_manager import (
    JwtTokenManager,
    TokenRevokedError,
    TokenVerificationError,
)
from tests.unit.fakes import (
    FakePasswordHasher,
    InMemorySessionStore,
    InMemoryUserRepository,
    make_user,
)


PASSWORD = "correct-horse-battery"


async def login(
    repo: InMemoryUserRepository, store: InMemorySessionStore, user
) -> TokenPairResponse:
    use_case = AuthenticateUserUseCase(
        user_repo=repo,
        hasher=FakePasswordHasher(),
        token_manager=JwtTokenManager(),
        session_store=store,
    )
    return await use_case.execute(AuthenticateUserRequest(email=str(user.email), password=PASSWORD))


def build_refresh_use_case(
    repo: InMemoryUserRepository, store: InMemorySessionStore
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        token_manager=JwtTokenManager(), session_store=store, user_repo=repo
    )


async def test_refresh_success_returns_new_pair() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)

    result = await build_refresh_use_case(repo, store).execute(
        RefreshTokenRequest(refresh_token=tokens.refresh_token)
    )

    assert result.access_token
    assert result.refresh_token != tokens.refresh_token


async def test_refresh_consumes_old_token_single_use() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)
    assert len(store.refresh_tokens) == 1

    await build_refresh_use_case(repo, store).execute(
        RefreshTokenRequest(refresh_token=tokens.refresh_token)
    )

    assert len(store.refresh_tokens) == 1
    old_claims = JwtTokenManager().decode_and_verify_token(
        tokens.refresh_token, expected_type="refresh"
    )
    assert not await store.is_refresh_token_valid(old_claims["family_id"], old_claims["jti"])


async def test_refresh_keeps_family_id_across_rotations() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)
    manager = JwtTokenManager()
    original_family = manager.decode_and_verify_token(
        tokens.refresh_token, expected_type="refresh"
    )["family_id"]

    result = await build_refresh_use_case(repo, store).execute(
        RefreshTokenRequest(refresh_token=tokens.refresh_token)
    )

    rotated_family = manager.decode_and_verify_token(
        result.refresh_token, expected_type="refresh"
    )["family_id"]
    assert rotated_family == original_family


async def test_refresh_restores_identity_claims_on_new_access_token() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD, is_superuser=True)
    await repo.save(user)
    tokens = await login(repo, store, user)

    result = await build_refresh_use_case(repo, store).execute(
        RefreshTokenRequest(refresh_token=tokens.refresh_token)
    )

    claims = JwtTokenManager().decode_and_verify_token(result.access_token, expected_type="access")
    assert claims["is_superuser"] is True
    assert claims["username"] == user.username


async def test_replaying_rotated_token_revokes_entire_family() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)
    use_case = build_refresh_use_case(repo, store)

    rotated = await use_case.execute(RefreshTokenRequest(refresh_token=tokens.refresh_token))

    with pytest.raises(TokenRevokedError):
        await use_case.execute(RefreshTokenRequest(refresh_token=tokens.refresh_token))

    assert store.refresh_tokens == {}
    with pytest.raises(TokenRevokedError):
        await use_case.execute(RefreshTokenRequest(refresh_token=rotated.refresh_token))


async def test_refresh_after_logout_is_rejected() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)

    family_id = JwtTokenManager().decode_and_verify_token(
        tokens.refresh_token, expected_type="refresh"
    )["family_id"]
    await LogoutUseCase(store).execute(family_id)

    with pytest.raises(TokenRevokedError):
        await build_refresh_use_case(repo, store).execute(
            RefreshTokenRequest(refresh_token=tokens.refresh_token)
        )


async def test_refresh_rejected_when_user_deleted() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)

    repo._users.clear()

    with pytest.raises(TokenRevokedError):
        await build_refresh_use_case(repo, store).execute(
            RefreshTokenRequest(refresh_token=tokens.refresh_token)
        )
    assert store.refresh_tokens == {}


async def test_refresh_rejected_when_user_deactivated() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)

    user.is_active = False

    with pytest.raises(TokenRevokedError):
        await build_refresh_use_case(repo, store).execute(
            RefreshTokenRequest(refresh_token=tokens.refresh_token)
        )
    assert store.refresh_tokens == {}


async def test_refresh_rejects_access_token_in_place_of_refresh_token() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()
    user = make_user(password=PASSWORD)
    await repo.save(user)
    tokens = await login(repo, store, user)

    with pytest.raises(TokenVerificationError):
        await build_refresh_use_case(repo, store).execute(
            RefreshTokenRequest(refresh_token=tokens.access_token)
        )


async def test_refresh_rejects_garbage_token() -> None:
    repo, store = InMemoryUserRepository(), InMemorySessionStore()

    with pytest.raises(TokenVerificationError):
        await build_refresh_use_case(repo, store).execute(
            RefreshTokenRequest(refresh_token="not.a.jwt")
        )
