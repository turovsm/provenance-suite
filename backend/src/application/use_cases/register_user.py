import uuid
from dataclasses import dataclass

from src.application.exceptions import UserAlreadyExistsError
from src.application.interfaces.crypto import PasswordHasher
from src.application.repositories.user import UserRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress


@dataclass(frozen=True, slots=True)
class RegisterUserRequest:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RegisterUserResponse:
    id: uuid.UUID
    email: str
    is_active: bool


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        """Execute registration verification operations checks."""
        # 1. Verify that the email fits the email pattern
        email_vo = EmailAddress(request.email)

        # 2. Check if user already exists
        existing_user = await self._user_repo.find_by_email(email_vo)
        if existing_user is not None:
            msg = f"Identity record with email '{email_vo}' already exists within system tracks."
            raise UserAlreadyExistsError(msg)

        # 3. Hash password
        hashed_password = self._hasher.hash_password(request.password)

        # 4. Generate domain entity for the user
        new_user = User.create_new(email=email_vo, hashed_password=hashed_password)

        # 5. Save user into the database
        await self._user_repo.save(new_user)

        return RegisterUserResponse(
            id=new_user.id,
            email=str(new_user.email),
            is_active=new_user.is_active,
        )
