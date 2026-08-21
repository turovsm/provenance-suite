import uuid
from dataclasses import dataclass

from src.application.exceptions import InvalidCredentialsError, UserDeactivatedError
from src.application.interfaces.crypto import PasswordHasher
from src.application.repositories.user import UserRepository
from src.domain.value_objects.email import EmailAddress
from src.infrastructure.crypto.token_manager import (
    JwtTokenManager,
    RedisTokenSessionStore,
    TokenRevokedError,
)


@dataclass(frozen=True, slots=True)
class AuthenticateUserRequest:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class TokenPairResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        hasher: PasswordHasher,
        token_manager: JwtTokenManager,
        session_store: RedisTokenSessionStore,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_manager = token_manager
        self._session_store = session_store

    async def execute(self, request: AuthenticateUserRequest) -> TokenPairResponse:
        email_vo = EmailAddress(request.email)
        user = await self._user_repo.find_by_email(email_vo)

        if user is None:
            self._hasher.perform_dummy_verification()
            raise InvalidCredentialsError("Invalid email or password.")

        if not self._hasher.verify_password(user.hashed_password, request.password):
            raise InvalidCredentialsError("Invalid email or password.")

        if not user.is_active:
            raise UserDeactivatedError("This account has been deactivated.")

        access_token, refresh_token, family_id, jti = self._token_manager.generate_token_pair(
            subject=str(user.id),
            extra_claims={"role": user.role.value, "username": user.username},
        )

        await self._session_store.register_refresh_token(
            user_id=str(user.id), family_id=family_id, jti=jti
        )

        return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)


@dataclass(frozen=True, slots=True)
class RefreshTokenRequest:
    refresh_token: str


class RefreshTokenUseCase:
    def __init__(
        self,
        token_manager: JwtTokenManager,
        session_store: RedisTokenSessionStore,
        user_repo: UserRepository,
    ) -> None:
        self._token_manager = token_manager
        self._session_store = session_store
        self._user_repo = user_repo

    async def execute(self, request: RefreshTokenRequest) -> TokenPairResponse:
        payload = self._token_manager.decode_and_verify_token(
            request.refresh_token, expected_type="refresh"
        )
        user_id = payload["sub"]
        family_id = payload["family_id"]
        jti = payload["jti"]

        is_valid = await self._session_store.is_refresh_token_valid(family_id, jti)
        if not is_valid:
            await self._session_store.invalidate_token_family(family_id)
            raise TokenRevokedError("Session expired for security reasons. Please log in again.")

        await self._session_store.revoke_refresh_token(family_id, jti)

        user = await self._user_repo.find_by_id(uuid.UUID(user_id))
        if user is None or not user.is_active:
            await self._session_store.invalidate_token_family(family_id)
            msg = "Session expired or account is deactivated. Please log in again."
            raise TokenRevokedError(msg)

        access_token, new_refresh_token, _, new_jti = self._token_manager.generate_token_pair(
            subject=user_id,
            family_id=family_id,
            extra_claims={"role": user.role.value, "username": user.username},
        )

        await self._session_store.register_refresh_token(
            user_id=user_id, family_id=family_id, jti=new_jti
        )

        return TokenPairResponse(access_token=access_token, refresh_token=new_refresh_token)


class LogoutUseCase:
    def __init__(self, session_store: RedisTokenSessionStore) -> None:
        self._session_store = session_store

    async def execute(self, family_id: str) -> None:
        await self._session_store.invalidate_token_family(family_id)
