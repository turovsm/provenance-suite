import uuid

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.infrastructure.crypto.token_manager import (
    JwtTokenManager,
    RedisTokenSessionStore,
    TokenVerificationError,
)
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import get_redis


security_scheme = HTTPBearer(scheme_name="Bearer JWT Token Authorization", auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:
    token_manager = JwtTokenManager()
    session_store = RedisTokenSessionStore(redis)
    user_repository = SqlAlchemyUserRepository(session)

    try:
        claims = token_manager.decode_and_verify_token(
            credentials.credentials, expected_type="access"
        )
        jti = claims["jti"]

        if await session_store.is_access_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has been revoked.",
            )

        subject = claims.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failure: Missing identity subject claim.",
            )

        user_id = uuid.UUID(subject)

    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Cryptographic payload verification rejected: {str(exc)}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token identity format violates system UUID tracking layout.",
        ) from exc

    user = await user_repository.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Target identity record no longer exists.",
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User account is suspended.",
        )
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrative permissions required.",
        )
    return current_user
