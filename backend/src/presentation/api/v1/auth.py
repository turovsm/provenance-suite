import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import InvalidCredentialsError, UserDeactivatedError
from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserUseCase,
    LogoutUseCase,
    RefreshTokenRequest,
    RefreshTokenUseCase,
)
from src.infrastructure.crypto.hasher import PasswordHasherEngine
from src.infrastructure.crypto.token_manager import (
    JwtTokenManager,
    RedisTokenSessionStore,
    TokenRevokedError,
    TokenVerificationError,
)
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import get_redis
from src.presentation.schemas.auth import (
    RefreshTokenRequestSchema,
    TokenResponseSchema,
    UserLoginRequestSchema,
)


router = APIRouter(prefix="/auth", tags=["Identity Session Authentication Plane"])


@router.post(
    "/login",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Authenticate profile to receive access token + rotating refresh token.",
)
async def login_endpoint(
    payload: UserLoginRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponseSchema:
    user_repository = SqlAlchemyUserRepository(session)
    crypto_engine = PasswordHasherEngine()
    token_manager = JwtTokenManager()
    session_store = RedisTokenSessionStore(redis)

    use_case = AuthenticateUserUseCase(
        user_repo=user_repository,
        hasher=crypto_engine,
        token_manager=token_manager,
        session_store=session_store,
    )

    try:
        res = await use_case.execute(
            AuthenticateUserRequest(email=payload.email, password=payload.password)
        )
        return TokenResponseSchema(
            access_token=res.access_token,
            refresh_token=res.refresh_token,
            token_type=res.token_type,
            expires_in=res.expires_in,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserDeactivatedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/refresh",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and exchange for fresh token pair.",
)
async def refresh_endpoint(
    payload: RefreshTokenRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> TokenResponseSchema:
    token_manager = JwtTokenManager()
    session_store = RedisTokenSessionStore(redis)
    user_repository = SqlAlchemyUserRepository(session)
    use_case = RefreshTokenUseCase(
        token_manager=token_manager,
        session_store=session_store,
        user_repo=user_repository,
    )

    try:
        res = await use_case.execute(RefreshTokenRequest(refresh_token=payload.refresh_token))
        return TokenResponseSchema(
            access_token=res.access_token,
            refresh_token=res.refresh_token,
            token_type=res.token_type,
            expires_in=res.expires_in,
        )
    except (TokenVerificationError, TokenRevokedError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke active refresh token family session.",
)
async def logout_endpoint(
    payload: RefreshTokenRequestSchema,
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    token_manager = JwtTokenManager()
    session_store = RedisTokenSessionStore(redis)

    try:
        claims = token_manager.decode_and_verify_token(
            payload.refresh_token, expected_type="refresh"
        )
        family_id = claims["family_id"]
        use_case = LogoutUseCase(session_store)
        await use_case.execute(family_id)
    except TokenVerificationError:
        pass
