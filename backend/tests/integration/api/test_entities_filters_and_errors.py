import uuid

from httpx import AsyncClient

from tests.integration.api.conftest import bearer


async def test_event_filtering_by_status_and_date_range(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    # Seed events with distinct statuses and dates
    events = [
        {
            "short_name": "EV-HELD",
            "start_date": "2024-05-01",
            "end_date": "2024-05-02",
            "status": "HELD",
        },
        {
            "short_name": "EV-UPCOMING",
            "start_date": "2026-10-01",
            "end_date": "2026-10-02",
            "status": "UPCOMING",
        },
        {
            "short_name": "EV-CANCELLED",
            "start_date": "2023-01-01",
            "end_date": "2023-01-02",
            "status": "CANCELLED",
        },
        {
            "short_name": "EV-POSTPONED",
            "start_date": "2022-08-15",
            "end_date": "2022-08-15",
            "status": "POSTPONED",
        },
    ]
    for ev in events:
        res = await client.post("/api/v1/entities/events", json=ev, headers=bearer(admin_tokens))
        assert res.status_code == 201

    # 1. Filter by Status
    held_res = await client.get("/api/v1/entities/events?status=HELD", headers=bearer(user_tokens))
    assert held_res.status_code == 200
    assert held_res.json()["total_count"] == 1
    assert held_res.json()["items"][0]["short_name"] == "EV-HELD"

    multi_status = await client.get(
        "/api/v1/entities/events?status=HELD,UPCOMING", headers=bearer(user_tokens)
    )
    assert multi_status.json()["total_count"] == 2

    # 2. Filter by Date Bounds
    range_res = await client.get(
        "/api/v1/entities/events?date_from=2024-01-01&date_to=2025-01-01",
        headers=bearer(user_tokens),
    )
    assert range_res.json()["total_count"] == 1
    assert range_res.json()["items"][0]["short_name"] == "EV-HELD"

    # 3. Sorting by short_name and status
    sort_name_asc = await client.get(
        "/api/v1/entities/events?sort_by=short_name&sort_order=asc",
        headers=bearer(user_tokens),
    )
    assert sort_name_asc.json()["items"][0]["short_name"] == "EV-CANCELLED"

    sort_status_desc = await client.get(
        "/api/v1/entities/events?sort_by=status&sort_order=desc",
        headers=bearer(user_tokens),
    )
    assert sort_status_desc.status_code == 200


async def test_entity_404_not_found_branches(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    dummy_id = uuid.uuid4()

    # Artists 404
    assert (
        await client.get(f"/api/v1/entities/artists/{dummy_id}", headers=bearer(user_tokens))
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/entities/artists/{dummy_id}",
            json={"name_original": "x"},
            headers=bearer(admin_tokens),
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/entities/artists/{dummy_id}", headers=bearer(admin_tokens))
    ).status_code == 404

    # Franchises 404
    assert (
        await client.get(f"/api/v1/entities/franchises/{dummy_id}", headers=bearer(user_tokens))
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/entities/franchises/{dummy_id}",
            json={"name_original": "x"},
            headers=bearer(admin_tokens),
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/entities/franchises/{dummy_id}", headers=bearer(admin_tokens))
    ).status_code == 404

    # Labels 404
    assert (
        await client.get(f"/api/v1/entities/labels/{dummy_id}", headers=bearer(user_tokens))
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/entities/labels/{dummy_id}",
            json={"name_original": "x"},
            headers=bearer(admin_tokens),
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/entities/labels/{dummy_id}", headers=bearer(admin_tokens))
    ).status_code == 404

    # Publishers 404
    assert (
        await client.get(f"/api/v1/entities/publishers/{dummy_id}", headers=bearer(user_tokens))
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/entities/publishers/{dummy_id}",
            json={"name_original": "x"},
            headers=bearer(admin_tokens),
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/entities/publishers/{dummy_id}", headers=bearer(admin_tokens))
    ).status_code == 404

    # Events 404
    assert (
        await client.get(f"/api/v1/entities/events/{dummy_id}", headers=bearer(user_tokens))
    ).status_code == 404
    assert (
        await client.put(
            f"/api/v1/entities/events/{dummy_id}",
            json={"short_name": "x"},
            headers=bearer(admin_tokens),
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/v1/entities/events/{dummy_id}", headers=bearer(admin_tokens))
    ).status_code == 404
