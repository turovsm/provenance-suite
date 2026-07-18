import uuid
from abc import ABC, abstractmethod

from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        pass

    @abstractmethod
    async def find_by_email(self, email: EmailAddress) -> User | None:
        pass
