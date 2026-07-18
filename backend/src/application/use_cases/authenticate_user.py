from dataclasses import dataclass

from src.application.exceptions import InvalidCredentialsError, UserDeactivatedError
from src.application.interfaces.crypto import PasswordHasher
from src.application.interfaces.token import TokenService
from src.application.repositories.user import UserRepository
from src.domain.value_objects.email import EmailAddress


@dataclass(frozen=True, slots=True)
class AuthenticateUserRequest:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class AuthenticateUserResponse:
    access_token: str
    token_type: str


class AuthenticateUserUseCase:
    def __init__(
        self, user_repo: UserRepository, hasher: PasswordHasher, token_service: TokenService
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher
        self._token_service = token_service

    async def execute(self, request: AuthenticateUserRequest) -> AuthenticateUserResponse:
        """Executes user authentication use case."""
        # 1. Find user by email
        email_vo = EmailAddress(request.email)
        user = await self._user_repo.find_by_email(email_vo)

        # 2. Fail if no such user
        if user is None:
            raise InvalidCredentialsError("Invalid email or password sequence provided.")

        # 3. Verify password and fail if it is incorrect
        is_valid = self._hasher.verify_password(user.hashed_password, request.password)
        if not is_valid:
            raise InvalidCredentialsError("Invalid email or password sequence provided.")

        # 4. Fail if user's account is deactivated
        if not user.is_active:
            raise UserDeactivatedError("Target authenticated identity profile is deactivated.")

        # 5. Generate auth token
        token = self._token_service.generate_access_token(
            subject=str(user.id), extra_claims={"is_superuser": user.is_superuser}
        )

        # 6. Grant token to the user
        return AuthenticateUserResponse(access_token=token, token_type="bearer")
