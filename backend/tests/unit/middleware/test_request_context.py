from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.presentation.middleware.request_context import RequestContextMiddleware


def build_context_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)

    @app.get("/test-header")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=build_context_app()), base_url="http://test"
    ) as http:
        yield http


async def test_request_id_generated_when_missing(client: AsyncClient) -> None:
    response = await client.get("/test-header")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10


async def test_request_id_propagates_existing(client: AsyncClient) -> None:
    custom_id = "custom-trace-uuid-12345"
    response = await client.get("/test-header", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


async def test_security_headers_present(client: AsyncClient) -> None:
    response = await client.get("/test-header")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
