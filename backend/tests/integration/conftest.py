from collections.abc import AsyncGenerator

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.db.models.base import BaseInfrastructureModel
from tests.conftest import test_database_name, test_engine


REQUIRED_EXTENSIONS = ("pg_trgm",)


async def _ensure_test_database_exists() -> None:
    db_name = test_database_name()
    try:
        conn = await asyncpg.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database="postgres",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Integration tests need PostgreSQL at "
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT} "
            f"(is `make db-up` running?). Connection failed: {exc!r}"
        ) from exc

    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    except asyncpg.DuplicateDatabaseError:
        pass
    except Exception as exc:
        raise RuntimeError(
            f"Could not create test database '{db_name}': {exc!r}. "
            f'Create it manually with: CREATE DATABASE "{db_name}";'
        ) from exc
    finally:
        await conn.close()


@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database_schema() -> AsyncGenerator[None, None]:
    await _ensure_test_database_exists()
    async with test_engine.begin() as conn:
        for extension in REQUIRED_EXTENSIONS:
            await conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{extension}"'))
        await conn.run_sync(BaseInfrastructureModel.metadata.drop_all)
        await conn.run_sync(BaseInfrastructureModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseInfrastructureModel.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        yield session

        await session.close()
        await transaction.rollback()
