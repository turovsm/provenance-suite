from datetime import UTC, datetime, timedelta
from typing import Any

from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError, decode, encode

from src.config import settings


class TokenError(Exception):
    """Base exception for all token-related processing errors."""


class TokenSerializationError(TokenError):
    """Signaled when token encryption or payload generation fails."""


class TokenVerificationError(TokenError):
    """Signaled when an inbound token is expired, warped, or structurally invalid."""


class JwtTokenManager:
    def __init__(self) -> None:
        self._secret_key = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._default_expiry = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def generate_access_token(
        self, subject: str, extra_claims: dict[str, Any] | None = None
    ) -> str:
        now = datetime.now(UTC)
        expiry_delta = timedelta(minutes=self._default_expiry)

        claims = {
            "sub": str(subject),
            "iat": now,
            "exp": now + expiry_delta,
            "nbf": now,
        }

        if extra_claims:
            # Shield structural invariants from payload modification attacks
            sanitized_claims = {k: v for k, v in extra_claims.items() if k not in claims}
            claims.update(sanitized_claims)

        try:
            return encode(claims, self._secret_key, algorithm=self._algorithm)
        except PyJWTError as e:
            msg = "Internal hardware token signing sequence generation layer error occurred."
            raise TokenSerializationError(msg) from e

    def decode_and_verify_token(self, token: str) -> dict[str, Any]:
        try:
            return decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "sub"]},
            )
        except ExpiredSignatureError as e:
            raise TokenVerificationError("Inbound token validity timeline has expired.") from e
        except InvalidTokenError as e:
            raise TokenVerificationError("Provided signature hash mismatch or malformed.") from e
