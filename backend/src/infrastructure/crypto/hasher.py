from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, VerificationError

from src.config import settings


class PasswordHasherEngine:
    def __init__(self) -> None:
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
            secret=settings.SECURITY_PEPPER.encode("utf-8"),
        )

    def hash_password(self, password: str) -> str:
        try:
            return self._hasher.hash(password)
        except Argon2Error as e:
            msg = "Critical memory execution derivation failure inside hashing engine."
            raise RuntimeError(msg) from e

    def verify_password(self, hash_string: str, password: str) -> bool:
        try:
            return self._hasher.verify(hash_string, password)
        except VerificationError:
            return False
        except Argon2Error as e:
            msg = "Critical verification subsystem computational variance failure."
            raise RuntimeError(msg) from e

    def check_needs_rehash(self, hash_string: str) -> bool:
        return self._hasher.check_needs_rehash(hash_string)
