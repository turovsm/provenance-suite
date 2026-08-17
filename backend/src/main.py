import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import close_redis_pool, get_redis, init_redis_pool
from src.infrastructure.storage.object_storage import MinioObjectStorageService
from src.presentation.api.v1 import auth_router, entities_router, music_router, user_router
from src.presentation.middleware.exception_handlers import register_exception_handlers
from src.presentation.middleware.rate_limit import (
    RedisSlidingWindowRateLimiter,
    RequestSizeLimitMiddleware,
)
from src.presentation.middleware.request_context import RequestContextMiddleware
from src.presentation.openapi import OPENAPI_TAGS


logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("provenance")

API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_app_instance: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing Redis connection pool...")
    init_redis_pool()

    try:
        logger.info("Initializing MinIO bucket storage policy...")
        storage_service = MinioObjectStorageService()
        await anyio.to_thread.run_sync(storage_service.ensure_bucket_and_policy)
    except Exception as exc:
        logger.warning("MinIO initialization warning: %s", exc)

    yield
    logger.info("Closing Redis connection pool...")
    await close_redis_pool()


app = FastAPI(
    title="Provenance Suite API",
    description="Digital asset tracking and music archival engine.",
    version="0.1.0",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

register_exception_handlers(app)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RedisSlidingWindowRateLimiter)

app.include_router(user_router, prefix=API_V1_PREFIX)
app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(music_router, prefix=API_V1_PREFIX)
app.include_router(entities_router, prefix=API_V1_PREFIX)


@app.get(
    "/health",
    tags=["System Stability Checks"],
    status_code=status.HTTP_200_OK,
    summary="Execute real-time infrastructure readiness checks (PostgreSQL & Redis).",
)
async def health_check(
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    postgres_status = "ok"
    redis_status = "ok"

    try:
        await asyncio.wait_for(session.execute(select(1)), timeout=2.0)
    except Exception as exc:
        logger.exception("Health probe PostgreSQL check failed: %s", exc)
        postgres_status = "error"

    try:
        await asyncio.wait_for(redis.ping(), timeout=2.0)
    except Exception as exc:
        logger.exception("Health probe Redis check failed: %s", exc)
        redis_status = "error"

    overall_healthy = postgres_status == "ok" and redis_status == "ok"

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "service": "provenance-core-backend",
        "version": "0.1.0",
        "checks": {
            "database": postgres_status,
            "cache": redis_status,
        },
    }
