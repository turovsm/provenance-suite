from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.exceptions import UserAlreadyExistsError
from src.application.use_cases.register_user import (
    RegisterUserRequest,
    RegisterUserUseCase,
)
from src.domain.exceptions import InvalidEmailError
from src.infrastructure.crypto.hasher import PasswordHasherEngine
from src.infrastructure.db.repositories.user import SqlAlchemyUserRepository
from src.infrastructure.db.session import get_async_database_session
from src.presentation.schemas.user import UserRegisterRequestSchema, UserResponseSchema


router = APIRouter(prefix="/users", tags=["Users Identity Engine"])


@router.post(
    "",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a fresh cryptographically secure user profile handle.",
)
async def register_user_endpoint(
    payload: UserRegisterRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
) -> UserResponseSchema:
    # 1. Get instances
    user_repository = SqlAlchemyUserRepository(session)
    crypto_engine = PasswordHasherEngine()

    # 2. Create user registration use case
    use_case = RegisterUserUseCase(user_repo=user_repository, hasher=crypto_engine)

    # 3. Create use case request
    use_case_request = RegisterUserRequest(email=payload.email, password=payload.password)

    try:
        # 4. Execute user registration use case
        use_case_response = await use_case.execute(use_case_request)

        # 5. Commit database session
        await session.commit()

        # 6. Get user from the database
        db_user = await user_repository.find_by_id(use_case_response.id)
        if db_user is None:
            msg = "Critical internal transaction trace discrepancy encountered on row commit."
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=msg,
            )

        return UserResponseSchema(
            id=db_user.id,
            email=str(db_user.email),
            is_active=db_user.is_active,
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

    except (UserAlreadyExistsError, InvalidEmailError) as exc:
        # Rollback target records on transaction state exceptions conflicts
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    except Exception as exc:
        # Shield internal stack traces from leaking
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected storage exception breakdown occurred during synchronization.",
        ) from exc
