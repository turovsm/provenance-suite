from enum import StrEnum


class UserRole(StrEnum):
    GUEST = "guest"
    USER = "user"
    TRUSTED = "trusted"
    MODERATOR = "moderator"
    ADMIN = "admin"

    @property
    def level(self) -> int:
        levels = {
            UserRole.GUEST: 0,
            UserRole.USER: 1,
            UserRole.TRUSTED: 2,
            UserRole.MODERATOR: 3,
            UserRole.ADMIN: 4,
        }
        return levels[self]

    def has_permission(self, required_role: "UserRole") -> bool:
        return self.level >= required_role.level

    @classmethod
    def from_string(cls, value: str | None) -> "UserRole":
        if not value:
            return cls.USER
        normalized = value.strip().lower()
        for role in cls:
            if role.value == normalized:
                return role
        return cls.USER
