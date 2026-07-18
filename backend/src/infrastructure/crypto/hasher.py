from hashlib import sha256
from hmac import new

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
        )
        self._pepper = settings.SECURITY_PEPPER.encode("utf-8")

    def _pre_hash(self, password: str) -> str:
        return new(
            key=self._pepper,
            msg=password.encode("utf-8"),
            digestmod=sha256,
        ).hexdigest()

    def hash_password(self, password: str) -> str:
        try:
            pre_hashed = self._pre_hash(password)
            return self._hasher.hash(pre_hashed)
        except Argon2Error as e:
            msg = "Critical memory execution derivation failure inside hashing engine."
            raise RuntimeError(msg) from e

    def verify_password(self, hash_string: str, password: str) -> bool:
        try:
            pre_hashed = self._pre_hash(password)
            return self._hasher.verify(hash_string, pre_hashed)
        except VerificationError:
            return False
        except Argon2Error as e:
            msg = "Critical verification subsystem computational variance failure."
            raise RuntimeError(msg) from e

    def check_needs_rehash(self, hash_string: str) -> bool:
        return self._hasher.check_needs_rehash(hash_string)
