from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import InvalidCredentialsError, UserDeactivatedError
from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserUseCase,
)
from src.infrastructure.crypto.hasher import PasswordHasherEngine
from src.infrastructure.crypto.token_manager import JwtTokenManager
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.presentation.schemas.auth import TokenResponseSchema, UserLoginRequestSchema


router = APIRouter(prefix="/auth", tags=["Identity Session Authentication Plane"])


@router.post(
    "/login",
    response_model=TokenResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user profile records to exchange a fresh token string payload.",
)
async def login_endpoint(
    payload: UserLoginRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),  # noqa: B008
) -> TokenResponseSchema:
    # 1. Create engine/session instances
    user_repository = SqlAlchemyUserRepository(session)
    crypto_engine = PasswordHasherEngine()
    token_engine = JwtTokenManager()

    # 2. Initiate use case
    use_case = AuthenticateUserUseCase(
        user_repo=user_repository, hasher=crypto_engine, token_service=token_engine
    )
    use_case_request = AuthenticateUserRequest(email=payload.email, password=payload.password)

    # 3. Attempt to run auth use case
    try:
        use_case_response = await use_case.execute(use_case_request)
        return TokenResponseSchema(
            access_token=use_case_response.access_token,
            token_type=use_case_response.token_type,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except UserDeactivatedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Exception as exc:
        msg = "Unexpected security system verification anomaly breakdown occurred."
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from exc
