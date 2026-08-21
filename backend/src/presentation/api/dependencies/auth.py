import uuid
from collections.abc import Callable

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.crypto.token_manager import (
    JwtTokenManager,
    RedisTokenSessionStore,
    TokenVerificationError,
)
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import get_redis


security_scheme = HTTPBearer(scheme_name="Bearer JWT Token Authorization", auto_error=True)
optional_security_scheme = HTTPBearer(
    scheme_name="Bearer JWT Token Authorization", auto_error=False
)


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
                detail="Session has expired. Please log in again.",
            )

        subject = claims.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token. Please log in again.",
            )

        user_id = uuid.UUID(subject)

    except TokenVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session identifier. Please log in again.",
        ) from exc

    user = await user_repository.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found. Please log in again.",
        )

    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security_scheme),
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> User | None:
    if not credentials:
        return None

    token_manager = JwtTokenManager()
    session_store = RedisTokenSessionStore(redis)
    user_repository = SqlAlchemyUserRepository(session)

    try:
        claims = token_manager.decode_and_verify_token(
            credentials.credentials, expected_type="access"
        )
        jti = claims.get("jti")
        if not jti or await session_store.is_access_token_blacklisted(jti):
            return None

        subject = claims.get("sub")
        if not subject:
            return None

        user_id = uuid.UUID(subject)
        user = await user_repository.find_by_id(user_id)
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )
    return current_user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            roles_str = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {roles_str}.",
            )
        return current_user

    return dependency


def require_min_role(min_role: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role.has_permission(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Minimum required role tier: {min_role.value}.",
            )
        return current_user

    return dependency


require_admin = require_role(UserRole.ADMIN)
require_moderator_or_admin = require_min_role(UserRole.MODERATOR)
require_trusted = require_min_role(UserRole.TRUSTED)
