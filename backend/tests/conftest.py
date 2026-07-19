from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.infrastructure.db.models.base import BaseInfrastructureModel


test_engine: AsyncEngine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    connect_args={"command_timeout": 5.0},
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database_schema() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseInfrastructureModel.metadata.drop_all)
        await conn.run_sync(BaseInfrastructureModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseInfrastructureModel.metadata.drop_all)


@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        yield session

        await session.close()
        await transaction.rollback()
