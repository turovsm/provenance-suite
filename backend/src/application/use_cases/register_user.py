import uuid
from dataclasses import dataclass

from src.application.exceptions import UserAlreadyExistsError
from src.application.interfaces.crypto import PasswordHasher
from src.application.repositories.user import UserRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole


@dataclass(frozen=True, slots=True)
class RegisterUserRequest:
    username: str
    email: str
    password: str
    role: UserRole = UserRole.USER


@dataclass(frozen=True, slots=True)
class RegisterUserResponse:
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool


class RegisterUserUseCase:
    def __init__(self, user_repo: UserRepository, hasher: PasswordHasher) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    async def execute(self, request: RegisterUserRequest) -> RegisterUserResponse:
        email_vo = EmailAddress(request.email)

        if await self._user_repo.find_by_username(request.username):
            raise UserAlreadyExistsError(f"Username '{request.username}' is already taken.")

        if await self._user_repo.find_by_email(email_vo):
            raise UserAlreadyExistsError(f"Email '{email_vo}' is already registered.")

        hashed_password = self._hasher.hash_password(request.password)
        new_user = User.create_new(
            username=request.username,
            email=email_vo,
            hashed_password=hashed_password,
            role=request.role,
        )

        await self._user_repo.save(new_user)

        return RegisterUserResponse(
            id=new_user.id,
            username=new_user.username,
            email=str(new_user.email),
            role=new_user.role,
            is_active=new_user.is_active,
        )
