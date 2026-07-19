from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.exceptions import InvalidCredentialsError
from src.application.interfaces.crypto import PasswordHasher
from src.application.interfaces.token import TokenService
from src.application.repositories.user import UserRepository
from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserUseCase,
)


@pytest.mark.asyncio
async def test_authentication_failure_on_missing_identity() -> None:
    """Verifies authentication triggers an error if no user matches the target email handle."""
    mock_user_repo = MagicMock(spec=UserRepository)
    mock_user_repo.find_by_email = AsyncMock(return_value=None)

    mock_hasher = MagicMock(spec=PasswordHasher)
    mock_token_service = MagicMock(spec=TokenService)

    use_case = AuthenticateUserUseCase(
        user_repo=mock_user_repo, hasher=mock_hasher, token_service=mock_token_service
    )
    request = AuthenticateUserRequest(email="unknown@vault.io", password="any_password_123")

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(request)

    mock_user_repo.find_by_email.assert_awaited_once()
