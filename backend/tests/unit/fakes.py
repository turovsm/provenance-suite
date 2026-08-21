import uuid

from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole


class FakePasswordHasher:
    def __init__(self) -> None:
        self.dummy_verification_calls = 0

    @staticmethod
    def hash_password(password: str) -> str:
        return f"hashed::{password}"

    @staticmethod
    def verify_password(hash_string: str, password: str) -> bool:
        return hash_string == f"hashed::{password}"

    def perform_dummy_verification(self) -> None:
        self.dummy_verification_calls += 1


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: dict[uuid.UUID, User] = {}

    async def save(self, user: User) -> None:
        self._users[user.id] = user

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)

    async def find_by_email(self, email: EmailAddress) -> User | None:
        for user in self._users.values():
            if str(user.email) == str(email):
                return user
        return None

    async def find_by_username(self, username: str) -> User | None:
        for user in self._users.values():
            if user.username == username:
                return user
        return None


class InMemorySessionStore:
    def __init__(self) -> None:
        self.refresh_tokens: dict[str, str] = {}
        self.blacklisted_access: set[str] = set()

    async def register_refresh_token(
        self, user_id: str, family_id: str, jti: str, _ttl_days: int = 30
    ) -> None:
        self.refresh_tokens[f"{family_id}:{jti}"] = user_id

    async def is_refresh_token_valid(self, family_id: str, jti: str) -> bool:
        return f"{family_id}:{jti}" in self.refresh_tokens

    async def revoke_refresh_token(self, family_id: str, jti: str) -> None:
        self.refresh_tokens.pop(f"{family_id}:{jti}", None)

    async def invalidate_token_family(self, family_id: str) -> None:
        stale = [k for k in self.refresh_tokens if k.startswith(f"{family_id}:")]
        for key in stale:
            del self.refresh_tokens[key]

    async def blacklist_access_token(self, jti: str, _ttl_seconds: int = 900) -> None:
        self.blacklisted_access.add(jti)

    async def is_access_token_blacklisted(self, jti: str) -> bool:
        return jti in self.blacklisted_access


def make_user(
    *,
    username: str = "collector",
    email: str = "collector@vault.io",
    password: str = "correct-horse-battery",
    role: UserRole = UserRole.USER,
    is_active: bool = True,
) -> User:
    return User(
        id=uuid.uuid4(),
        username=username,
        email=EmailAddress(email),
        hashed_password=FakePasswordHasher().hash_password(password),
        role=role,
        is_active=is_active,
    )
