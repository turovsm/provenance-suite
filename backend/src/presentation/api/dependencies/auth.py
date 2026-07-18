import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.infrastructure.crypto.token_manager import JwtTokenManager, TokenVerificationError
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session


security_scheme = HTTPBearer(
    scheme_name="Bearer JWT Token Authorization Gateway Engine", auto_error=True
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_async_database_session),
) -> User:
    token_manager = JwtTokenManager()
    user_repository = SqlAlchemyUserRepository(session)

    try:
        # 1. Parse payload hashes and verify signature validity timelines via .credentials
        claims = token_manager.decode_and_verify_token(credentials.credentials)

        subject = claims.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failure: Missing identity subject pointer tracking claim.",
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
            detail="Token identity tracker format violates system UUID tracking layout.",
        ) from exc

    # 2. Extract database profile traces matching the validated index tracking key
    user = await user_repository.find_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Target identity record no longer exists inside active authorization tracks.",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Authenticated profile token handle is suspended.",
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Required administrative authorization permissions missing.",
        )
    return current_user
