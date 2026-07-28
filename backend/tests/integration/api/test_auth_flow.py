import uuid

from httpx import AsyncClient

from tests.integration.api.conftest import (
    TEST_PASSWORD,
    bearer,
    login_account,
    register_account,
)


async def test_register_returns_created_profile_without_secrets(client: AsyncClient) -> None:
    body = await register_account(client, "fresh_user", "fresh@vault.io")

    assert body["username"] == "fresh_user"
    assert body["email"] == "fresh@vault.io"
    assert body["is_active"] is True
    assert body["is_superuser"] is False
    assert uuid.UUID(body["id"])
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_duplicate_username_conflicts(client: AsyncClient) -> None:
    await register_account(client, "dupe", "first@vault.io")
    response = await client.post(
        "/api/v1/users",
        json={"username": "dupe", "email": "second@vault.io", "password": TEST_PASSWORD},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDENTITY_CONFLICT"


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    await register_account(client, "first", "same@vault.io")
    response = await client.post(
        "/api/v1/users",
        json={"username": "second", "email": "same@vault.io", "password": TEST_PASSWORD},
    )
    assert response.status_code == 409


async def test_register_rejects_invalid_email_shape(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={"username": "x", "email": "not-an-email", "password": TEST_PASSWORD},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users",
        json={"username": "x", "email": "x@vault.io", "password": "short"},
    )
    assert response.status_code == 422


async def test_login_success_returns_bearer_pair(client: AsyncClient) -> None:
    await register_account(client, "login_user", "login@vault.io")
    tokens = await login_account(client, "login@vault.io")

    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"] and tokens["refresh_token"]
    assert tokens["expires_in"] > 0


async def test_login_wrong_password_unauthorized(client: AsyncClient) -> None:
    await register_account(client, "login_user", "login@vault.io")
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@vault.io", "password": "wrong-password-value"},
    )
    assert response.status_code == 401


async def test_login_unknown_email_unauthorized_with_generic_error(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@vault.io", "password": TEST_PASSWORD},
    )
    assert response.status_code == 401
    assert "ghost" not in response.text


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code in (401, 403)


async def test_me_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


async def test_me_returns_own_profile(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.get("/api/v1/users/me", headers=bearer(user_tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "regular_user"
    assert body["is_superuser"] is False


async def test_refresh_rotates_and_old_token_is_dead(client: AsyncClient) -> None:
    await register_account(client, "rotator", "rotate@vault.io")
    tokens = await login_account(client, "rotate@vault.io")

    first = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200
    rotated = first.json()
    assert rotated["refresh_token"] != tokens["refresh_token"]

    replay = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert replay.status_code == 401

    burned = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated["refresh_token"]}
    )
    assert burned.status_code == 401


async def test_refresh_chain_works_when_used_correctly(client: AsyncClient) -> None:
    await register_account(client, "chainer", "chain@vault.io")
    tokens = await login_account(client, "chain@vault.io")

    current = tokens["refresh_token"]
    for _ in range(3):
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": current})
        assert response.status_code == 200
        current = response.json()["refresh_token"]

    final_access = response.json()["access_token"]
    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {final_access}"})
    assert me.status_code == 200


async def test_refresh_rejects_access_token(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": user_tokens["access_token"]}
    )
    assert response.status_code == 401


async def test_logout_kills_refresh_session(client: AsyncClient) -> None:
    await register_account(client, "leaver", "leave@vault.io")
    tokens = await login_account(client, "leave@vault.io")

    logout = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout.status_code == 204

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401


async def test_logout_with_invalid_token_is_silent_no_content(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "garbage-token-value"}
    )
    assert response.status_code == 204
