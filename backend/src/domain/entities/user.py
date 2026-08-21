import uuid
from dataclasses import dataclass
from datetime import datetime

from src.domain.exceptions import DomainInvariantError
from src.domain.value_objects.email import EmailAddress


@dataclass(slots=True)
class User:
    id: uuid.UUID
    username: str
    email: EmailAddress
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create_new(cls, username: str, email: EmailAddress, hashed_password: str) -> "User":
        return cls(
            id=uuid.uuid4(),
            username=username.strip(),
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
        )

    def deactivate(self) -> None:
        if self.is_superuser:
            raise DomainInvariantError("Admin accounts cannot be deactivated.")
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
