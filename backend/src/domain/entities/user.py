import uuid
from dataclasses import dataclass

from src.domain.exceptions import DomainInvariantError
from src.domain.value_objects.email import EmailAddress


@dataclass(slots=True)
class User:
    id: uuid.UUID
    email: EmailAddress
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False

    @classmethod
    def create_new(cls, email: EmailAddress, hashed_password: str) -> "User":
        return cls(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
        )

    def deactivate(self) -> None:
        if self.is_superuser:
            msg = "Administrative core superuser accounts cannot be deactivated."
            raise DomainInvariantError(msg)
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
