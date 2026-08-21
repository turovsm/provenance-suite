import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.repositories.user import UserRepository
from src.domain.entities.user import User
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.db.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        role_val = (
            user.role if isinstance(user.role, UserRole) else UserRole.from_string(str(user.role))
        )

        if model is None:
            model = UserModel(
                id=user.id,
                username=user.username,
                email=str(user.email),
                hashed_password=user.hashed_password,
                role=role_val,
                is_active=user.is_active,
            )
            self._session.add(model)
        else:
            model.username = user.username
            model.email = str(user.email)
            model.hashed_password = user.hashed_password
            model.role = role_val
            model.is_active = user.is_active

    async def find_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_email(self, email: EmailAddress) -> User | None:
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        role_val = (
            model.role
            if isinstance(model.role, UserRole)
            else UserRole.from_string(str(model.role))
        )
        return User(
            id=model.id,
            username=model.username,
            email=EmailAddress(model.email),
            hashed_password=model.hashed_password,
            role=role_val,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
