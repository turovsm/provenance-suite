from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.register_user import (
    RegisterUserRequest,
    RegisterUserUseCase,
)
from src.domain.entities.user import User
from src.infrastructure.crypto.hasher import PasswordHasherEngine
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.presentation.api.dependencies import get_current_active_user
from src.presentation.schemas.user import UserRegisterRequestSchema, UserResponseSchema


router = APIRouter(prefix="/users", tags=["Users Identity Engine"])


@router.post(
    "",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a cryptographically secure user profile.",
)
async def register_user_endpoint(
    payload: UserRegisterRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
) -> UserResponseSchema:
    user_repository = SqlAlchemyUserRepository(session)
    crypto_engine = PasswordHasherEngine()

    use_case = RegisterUserUseCase(user_repo=user_repository, hasher=crypto_engine)
    use_case_request = RegisterUserRequest(
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
    use_case_response = await use_case.execute(use_case_request)
    await session.commit()

    db_user = await user_repository.find_by_id(use_case_response.id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete registration. Please try again.",
        )

    return UserResponseSchema(
        id=db_user.id,
        username=db_user.username,
        email=str(db_user.email),
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at,
        updated_at=db_user.updated_at,
    )


@router.get(
    "/me",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Retrieve active user profile parameters.",
)
async def get_authenticated_profile_endpoint(
    current_user: User = Depends(get_current_active_user),
) -> UserResponseSchema:
    if current_user.created_at is None or current_user.updated_at is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load user profile details.",
        )

    return UserResponseSchema(
        id=current_user.id,
        username=current_user.username,
        email=str(current_user.email),
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )
