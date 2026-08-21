import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.exceptions import DomainInvariantError
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole


@dataclass(slots=True)
class User:
    id: uuid.UUID
    username: str
    email: EmailAddress
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create_new(
        cls,
        username: str,
        email: EmailAddress,
        hashed_password: str,
        role: UserRole = UserRole.USER,
    ) -> "User":
        return cls(
            id=uuid.uuid4(),
            username=username.strip(),
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True,
        )

    def deactivate(self) -> None:
        if self.role == UserRole.ADMIN:
            raise DomainInvariantError("Admin accounts cannot be deactivated.")
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
