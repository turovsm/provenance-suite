"""API-level integration fixtures.

Drives the real FastAPI app over ASGI with:
  * a real PostgreSQL test database (schema managed by the root conftest),
  * fakeredis substituted for the Redis dependency,
  * per-test table truncation so each test starts from a clean slate.

Requires the docker-compose Postgres to be running locally (``make db-up``);
in CI the service containers provide it.
"""

from collections.abc import AsyncGenerator

import pytest
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.db.models.base import BaseInfrastructureModel
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import get_redis
from src.main import app
from tests.conftest import test_engine


TEST_PASSWORD = "integration-test-password"

api_session_factory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest.fixture()
async def fake_redis() -> AsyncGenerator[FakeAsyncRedis, None]:
    redis = FakeAsyncRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.fixture()
async def client(fake_redis: FakeAsyncRedis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        session = api_session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def override_get_redis() -> AsyncGenerator[FakeAsyncRedis, None]:
        yield fake_redis

    app.dependency_overrides[get_async_database_session] = override_get_session
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http

    app.dependency_overrides.clear()

    # Wipe all rows so the next test starts clean (schema itself stays).
    table_names = ", ".join(
        f'"{table.name}"' for table in BaseInfrastructureModel.metadata.sorted_tables
    )
    async with test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


async def register_account(client: AsyncClient, username: str, email: str) -> dict:
    response = await client.post(
        "/api/v1/users",
        json={"username": username, "email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login_account(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def promote_to_superuser(username: str) -> None:
    async with test_engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET is_superuser = true WHERE username = :u"), {"u": username}
        )


def bearer(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
async def user_tokens(client: AsyncClient) -> dict:
    await register_account(client, "regular_user", "regular@vault.io")
    return await login_account(client, "regular@vault.io")


@pytest.fixture()
async def admin_tokens(client: AsyncClient) -> dict:
    await register_account(client, "admin_user", "admin@vault.io")
    await promote_to_superuser("admin_user")
    return await login_account(client, "admin@vault.io")
