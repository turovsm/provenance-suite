from httpx import AsyncClient

from tests.integration.api.conftest import bearer


async def test_health_check_endpoint(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["cache"] == "ok"


async def test_franchise_crud_lifecycle(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    create_res = await client.post(
        "/api/v1/entities/franchises",
        json={"name_original": "Touhou Project", "franchise_type": "Game"},
        headers=bearer(admin_tokens),
    )
    assert create_res.status_code == 201
    f_id = create_res.json()["id"]

    detail_res = await client.get(
        f"/api/v1/entities/franchises/{f_id}", headers=bearer(user_tokens)
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["name_original"] == "Touhou Project"

    search_res = await client.get(
        "/api/v1/entities/franchises?query=Touhou", headers=bearer(user_tokens)
    )
    assert len(search_res.json()) == 1

    update_res = await client.put(
        f"/api/v1/entities/franchises/{f_id}",
        json={"name_original": "Touhou Project (Updated)", "franchise_type": "Danmaku"},
        headers=bearer(admin_tokens),
    )
    assert update_res.status_code == 200
    assert update_res.json()["franchise_type"] == "Danmaku"

    delete_res = await client.delete(
        f"/api/v1/entities/franchises/{f_id}", headers=bearer(admin_tokens)
    )
    assert delete_res.status_code == 204

    gone = await client.get(f"/api/v1/entities/franchises/{f_id}", headers=bearer(user_tokens))
    assert gone.status_code == 404


async def test_label_and_publisher_crud_lifecycle(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    label_res = await client.post(
        "/api/v1/entities/labels",
        json={"name_original": "Alstroemeria Records"},
        headers=bearer(admin_tokens),
    )
    assert label_res.status_code == 201
    l_id = label_res.json()["id"]

    l_update = await client.put(
        f"/api/v1/entities/labels/{l_id}",
        json={"description": "Doujin electronic label"},
        headers=bearer(admin_tokens),
    )
    assert l_update.status_code == 200
    assert l_update.json()["description"] == "Doujin electronic label"

    pub_res = await client.post(
        "/api/v1/entities/publishers",
        json={"name_original": "Frontier Works"},
        headers=bearer(admin_tokens),
    )
    assert pub_res.status_code == 201
    p_id = pub_res.json()["id"]

    p_detail = await client.get(f"/api/v1/entities/publishers/{p_id}", headers=bearer(user_tokens))
    assert p_detail.status_code == 200

    assert (
        await client.delete(f"/api/v1/entities/labels/{l_id}", headers=bearer(admin_tokens))
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/entities/publishers/{p_id}", headers=bearer(admin_tokens))
    ).status_code == 204
