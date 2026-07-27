from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.presentation.middleware.rate_limit import RequestSizeLimitMiddleware


def build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestSizeLimitMiddleware)

    @app.post("/upload")
    async def upload() -> dict[str, bool]:
        return {"ok": True}

    return app


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=build_app()), base_url="http://t") as http:
        yield http


async def test_payload_within_limit_passes(client: AsyncClient) -> None:
    response = await client.post("/upload", content=b"x" * 1024)
    assert response.status_code == 200


async def test_oversized_payload_rejected_with_413_not_500(client: AsyncClient) -> None:
    oversized = str(settings.MAX_UPLOAD_SIZE_BYTES + 1)
    response = await client.post("/upload", content=b"", headers={"Content-Length": oversized})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
