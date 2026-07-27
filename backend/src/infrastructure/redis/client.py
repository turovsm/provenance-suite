from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from src.config import settings


redis_client: Redis | None = None


def init_redis_pool() -> None:
    global redis_client
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis_pool() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


async def get_redis() -> AsyncGenerator[Redis, None]:
    if redis_client is None:
        raise RuntimeError("Redis connection pool is not initialized.")
    yield redis_client
