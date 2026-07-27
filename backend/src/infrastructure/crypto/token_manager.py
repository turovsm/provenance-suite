import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import redis.asyncio as aioredis
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError, decode, encode

from src.config import settings


class TokenError(Exception):
    """Base exception for token operations."""


class TokenSerializationError(TokenError):
    """Signaled when token encryption or payload generation fails."""


class TokenVerificationError(TokenError):
    """Signaled on invalid or expired token signatures."""


class TokenRevokedError(TokenError):
    """Signaled when a revoked refresh token is presented."""


class JwtTokenManager:
    def __init__(self) -> None:
        self._secret_key = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._access_expiry_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self._refresh_expiry_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def generate_token_pair(
        self,
        subject: str,
        family_id: str | None = None,
        extra_claims: dict[str, Any] | None = None,
    ) -> tuple[str, str, str, str]:
        now = datetime.now(UTC)
        fam_id = family_id or str(uuid.uuid4())
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        access_claims = {
            "sub": str(subject),
            "jti": access_jti,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expiry_minutes),
        }
        if extra_claims:
            access_claims.update({k: v for k, v in extra_claims.items() if k not in access_claims})

        refresh_claims = {
            "sub": str(subject),
            "jti": refresh_jti,
            "family_id": fam_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expiry_days),
        }

        try:
            access_token = encode(access_claims, self._secret_key, algorithm=self._algorithm)
            refresh_token = encode(refresh_claims, self._secret_key, algorithm=self._algorithm)
            return access_token, refresh_token, fam_id, refresh_jti
        except PyJWTError as e:
            raise TokenSerializationError("Failed to serialize cryptographic token pair.") from e

    def decode_and_verify_token(self, token: str, expected_type: str = "access") -> dict[str, Any]:
        try:
            payload = decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "sub", "jti"]},
            )
            if payload.get("type") != expected_type:
                raise TokenVerificationError(
                    f"Invalid token purpose. Expected type '{expected_type}'."
                )
            return payload
        except ExpiredSignatureError as e:
            raise TokenVerificationError("Token has expired.") from e
        except InvalidTokenError as e:
            raise TokenVerificationError("Cryptographic signature payload malformed.") from e


class RedisTokenSessionStore:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    async def register_refresh_token(
        self, user_id: str, family_id: str, jti: str, ttl_days: int = 30
    ) -> None:
        key = f"token:refresh:{family_id}:{jti}"
        ttl_seconds = ttl_days * 86400
        await self._redis.set(key, user_id, ex=ttl_seconds)

    async def is_refresh_token_valid(self, family_id: str, jti: str) -> bool:
        key = f"token:refresh:{family_id}:{jti}"
        return await self._redis.exists(key) == 1

    async def revoke_refresh_token(self, family_id: str, jti: str) -> None:
        await self._redis.delete(f"token:refresh:{family_id}:{jti}")

    async def invalidate_token_family(self, family_id: str) -> None:
        pattern = f"token:refresh:{family_id}:*"
        keys = [key async for key in self._redis.scan_iter(pattern)]
        if keys:
            await self._redis.delete(*keys)

    async def blacklist_access_token(self, jti: str, ttl_seconds: int = 900) -> None:
        await self._redis.set(f"token:blacklist:{jti}", "1", ex=ttl_seconds)

    async def is_access_token_blacklisted(self, jti: str) -> bool:
        return await self._redis.exists(f"token:blacklist:{jti}") == 1
