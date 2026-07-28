from collections.abc import AsyncGenerator

import pytest
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.infrastructure.redis import client as redis_module
from src.presentation.middleware.rate_limit import RedisSlidingWindowRateLimiter


def build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RedisSlidingWindowRateLimiter)

    @app.get("/api/v1/albums")
    async def read_endpoint() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/v1/albums")
    async def mutation_endpoint() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/v1/auth/login")
    async def login_endpoint() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture()
async def fake_redis() -> AsyncGenerator[FakeAsyncRedis, None]:
    redis = FakeAsyncRedis(decode_responses=True)
    original = redis_module.redis_client
    redis_module.redis_client = redis
    yield redis
    redis_module.redis_client = original
    await redis.flushall()
    await redis.aclose()


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=build_app())
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


async def test_limiter_is_active_with_redis_available(
    client: AsyncClient, fake_redis: FakeAsyncRedis
) -> None:
    limit = settings.RATE_LIMIT_AUTH_PER_MIN
    statuses = [(await client.post("/api/v1/auth/login")).status_code for _ in range(limit + 1)]
    assert statuses[-1] == 429
    assert all(code == 200 for code in statuses[:-1])


async def test_auth_bucket_is_stricter_than_read_bucket(
    client: AsyncClient, fake_redis: FakeAsyncRedis
) -> None:
    auth_limit = settings.RATE_LIMIT_AUTH_PER_MIN
    for _ in range(auth_limit + 1):
        await client.post("/api/v1/auth/login")
    assert (await client.post("/api/v1/auth/login")).status_code == 429
    assert (await client.get("/api/v1/albums")).status_code == 200


async def test_mutations_and_reads_use_separate_buckets(
    client: AsyncClient, fake_redis: FakeAsyncRedis
) -> None:
    mutation_limit = settings.RATE_LIMIT_MUTATION_PER_MIN
    for _ in range(mutation_limit + 1):
        await client.post("/api/v1/albums")
    assert (await client.post("/api/v1/albums")).status_code == 429
    assert (await client.get("/api/v1/albums")).status_code == 200


async def test_fail_open_without_redis(client: AsyncClient) -> None:
    assert redis_module.redis_client is None
    for _ in range(settings.RATE_LIMIT_AUTH_PER_MIN + 5):
        response = await client.post("/api/v1/auth/login")
        assert response.status_code == 200
