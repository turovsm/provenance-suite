import logging
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from src.config import settings
from src.infrastructure.redis import client as redis_module
from src.presentation.schemas.error import ErrorDetailSchema, ErrorResponseEnvelope


logger = logging.getLogger("provenance.ratelimit")


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    envelope = ErrorResponseEnvelope(
        status="error",
        error=ErrorDetailSchema(code=code, message=message, details=None),
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


class RedisSlidingWindowRateLimiter(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        redis = redis_module.redis_client
        if redis is None:
            logger.warning("Rate limiter inactive: Redis pool not initialized.")
            return await call_next(request)

        path = request.url.path
        client_ip = request.client.host if request.client else "127.0.0.1"

        if path.startswith(("/api/v1/auth/login", "/api/v1/auth/refresh")):
            limit = settings.RATE_LIMIT_AUTH_PER_MIN
            key = f"ratelimit:auth:{client_ip}"
        elif request.method in ("POST", "DELETE", "PUT", "PATCH"):
            limit = settings.RATE_LIMIT_MUTATION_PER_MIN
            key = f"ratelimit:mutation:{client_ip}"
        else:
            limit = settings.RATE_LIMIT_READ_PER_MIN
            key = f"ratelimit:read:{client_ip}"

        window = 60
        now = time.time()
        clear_before = now - window

        async with redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            res = await pipe.execute()

        request_count = res[2]
        if request_count > limit:
            return _error_response(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code="RATE_LIMIT_EXCEEDED",
                message="Rate limit exceeded. Throttling active request bursts.",
            )

        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            return _error_response(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                code="PAYLOAD_TOO_LARGE",
                message=f"Payload exceeds maximum size cap of {max_mb} MB.",
            )
        return await call_next(request)
