"""Album catalog API tests: authorization matrix, CRUD lifecycle, validation,
pagination, search, and changelog behavior."""

import uuid

from httpx import AsyncClient

from tests.integration.api.conftest import bearer


def minimal_album_payload(title: str = "Test Album") -> dict:
    return {
        "title_original": title,
        "original_folder_name": f"[2024] {title}",
        "storage_drive": "HDD-01",
        "relative_path": f"/music/{title}",
    }


def full_album_payload() -> dict:
    return {
        **minimal_album_payload("Full Aggregate Album"),
        "title_translated": "Translated Title",
        "release_year": 2023,
        "release_month": 11,
        "release_day": 3,
        "label": "Test Label",
        "publisher": "Test Publisher",
        "album_artist": {"name_original": "Composer X", "name_translated": "X"},
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "catalog_number": "TEST-001",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Opening Theme",
                        "duration_seconds": 245,
                        "artists": [{"name_original": "Composer X", "role": "Composer"}],
                    },
                    {
                        "track_number": 2,
                        "title_original": "Second Movement",
                        "is_instrumental": True,
                    },
                ],
            }
        ],
        "archives": [
            {
                "archive_name": "album-vol1.rar",
                "encryption_password": "unpack-me",
                "file_size_bytes": 734003200,
                "links": [
                    {"provider_name": "MirrorA", "download_url": "https://a.example/dl/1"},
                    {"provider_name": "MirrorB", "download_url": "https://b.example/dl/1"},
                ],
            }
        ],
        "external_links": [{"site_name": "VGMdb", "url": "https://vgmdb.example/album/1"}],
    }


# ---------------------------------------------------------------------------
# Authorization matrix
# ---------------------------------------------------------------------------


async def test_anonymous_cannot_list_albums(client: AsyncClient) -> None:
    response = await client.get("/api/v1/albums")
    assert response.status_code in (401, 403)


async def test_regular_user_can_list_albums(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.get("/api/v1/albums", headers=bearer(user_tokens))
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total_count"] == 0


async def test_regular_user_cannot_create_album(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.post(
        "/api/v1/albums", json=minimal_album_payload(), headers=bearer(user_tokens)
    )
    assert response.status_code == 403


async def test_regular_user_cannot_delete_album(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.delete(f"/api/v1/albums/{uuid.uuid4()}", headers=bearer(user_tokens))
    assert response.status_code == 403


async def test_anonymous_cannot_create_album(client: AsyncClient) -> None:
    response = await client.post("/api/v1/albums", json=minimal_album_payload())
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Create / read lifecycle
# ---------------------------------------------------------------------------


async def test_admin_creates_minimal_album(client: AsyncClient, admin_tokens: dict) -> None:
    response = await client.post(
        "/api/v1/albums", json=minimal_album_payload(), headers=bearer(admin_tokens)
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["title_original"] == "Test Album"
    assert body["total_discs"] == 0
    assert body["total_tracks"] == 0


async def test_admin_creates_full_aggregate_and_reads_it_back(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    created = await client.post(
        "/api/v1/albums", json=full_album_payload(), headers=bearer(admin_tokens)
    )
    assert created.status_code == 201, created.text
    assert created.json()["total_discs"] == 1
    assert created.json()["total_tracks"] == 2
    album_id = created.json()["album_id"]

    # A regular user can read the full detail
    detail = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(user_tokens))
    assert detail.status_code == 200
    body = detail.json()

    assert body["title_original"] == "Full Aggregate Album"
    assert body["release_year"] == 2023
    assert body["album_artist"]["name_original"] == "Composer X"

    assert len(body["discs"]) == 1
    tracks = body["discs"][0]["tracks"]
    assert [t["track_number"] for t in tracks] == [1, 2]
    assert tracks[0]["title_original"] == "Opening Theme"
    assert tracks[1]["is_instrumental"] is True

    assert len(body["archives"]) == 1
    assert len(body["archives"][0]["links"]) == 2
    assert body["external_links"][0]["site_name"] == "VGMdb"

    # Creation is recorded in the changelog
    assert len(body["changelogs"]) >= 1


async def test_album_appears_in_listing_after_creation(
    client: AsyncClient, admin_tokens: dict
) -> None:
    await client.post(
        "/api/v1/albums", json=minimal_album_payload("Listed Album"), headers=bearer(admin_tokens)
    )
    listing = await client.get("/api/v1/albums", headers=bearer(admin_tokens))
    assert listing.json()["total_count"] == 1
    assert listing.json()["items"][0]["title_original"] == "Listed Album"


async def test_get_detail_unknown_id_returns_404(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.get(f"/api/v1/albums/{uuid.uuid4()}", headers=bearer(user_tokens))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ALBUM_NOT_FOUND"


async def test_get_detail_malformed_uuid_returns_422(
    client: AsyncClient, user_tokens: dict
) -> None:
    response = await client.get("/api/v1/albums/not-a-uuid", headers=bearer(user_tokens))
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


async def test_create_rejects_missing_required_fields(
    client: AsyncClient, admin_tokens: dict
) -> None:
    response = await client.post(
        "/api/v1/albums",
        json={"title_translated": "only optional fields"},
        headers=bearer(admin_tokens),
    )
    assert response.status_code == 422
    fields = [err["field"] for err in response.json()["error"]["details"]]
    assert any("title_original" in f for f in fields)


async def test_create_rejects_out_of_range_release_year(
    client: AsyncClient, admin_tokens: dict
) -> None:
    payload = minimal_album_payload() | {"release_year": 1500}
    response = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update & changelog
# ---------------------------------------------------------------------------


async def test_update_same_album_id_records_changelog_diff(
    client: AsyncClient, admin_tokens: dict
) -> None:
    created = await client.post(
        "/api/v1/albums", json=full_album_payload(), headers=bearer(admin_tokens)
    )
    album_id = created.json()["album_id"]

    updated_payload = full_album_payload() | {
        "album_id": album_id,
        "title_original": "Full Aggregate Album (Remastered)",
    }
    updated = await client.post(
        "/api/v1/albums", json=updated_payload, headers=bearer(admin_tokens)
    )
    assert updated.status_code == 201

    detail = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    body = detail.json()
    assert body["title_original"] == "Full Aggregate Album (Remastered)"
    assert len(body["changelogs"]) >= 2

    # The listing contains exactly one album — update did not duplicate it.
    listing = await client.get("/api/v1/albums", headers=bearer(admin_tokens))
    assert listing.json()["total_count"] == 1


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_admin_delete_lifecycle(client: AsyncClient, admin_tokens: dict) -> None:
    created = await client.post(
        "/api/v1/albums", json=minimal_album_payload("Doomed"), headers=bearer(admin_tokens)
    )
    album_id = created.json()["album_id"]

    deleted = await client.delete(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    assert deleted.status_code == 204

    gone = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    assert gone.status_code == 404


async def test_delete_unknown_album_returns_404(client: AsyncClient, admin_tokens: dict) -> None:
    response = await client.delete(f"/api/v1/albums/{uuid.uuid4()}", headers=bearer(admin_tokens))
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Pagination & search
# ---------------------------------------------------------------------------


async def test_pagination_limits_and_counts(client: AsyncClient, admin_tokens: dict) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/albums",
            json=minimal_album_payload(f"Paginated {i}"),
            headers=bearer(admin_tokens),
        )

    page = await client.get(
        "/api/v1/albums", params={"limit": 2, "offset": 0}, headers=bearer(admin_tokens)
    )
    body = page.json()
    assert body["total_count"] == 3
    assert len(body["items"]) == 2

    rest = await client.get(
        "/api/v1/albums", params={"limit": 2, "offset": 2}, headers=bearer(admin_tokens)
    )
    assert len(rest.json()["items"]) == 1


async def test_pagination_rejects_invalid_bounds(client: AsyncClient, user_tokens: dict) -> None:
    response = await client.get("/api/v1/albums", params={"limit": 0}, headers=bearer(user_tokens))
    assert response.status_code == 422
    response = await client.get(
        "/api/v1/albums", params={"limit": 101}, headers=bearer(user_tokens)
    )
    assert response.status_code == 422


async def test_search_filters_by_title(client: AsyncClient, admin_tokens: dict) -> None:
    await client.post(
        "/api/v1/albums",
        json=minimal_album_payload("Symphonic Suite Alpha"),
        headers=bearer(admin_tokens),
    )
    await client.post(
        "/api/v1/albums",
        json=minimal_album_payload("Piano Collection Beta"),
        headers=bearer(admin_tokens),
    )

    hits = await client.get(
        "/api/v1/albums", params={"query": "symphonic"}, headers=bearer(admin_tokens)
    )
    body = hits.json()
    assert body["total_count"] == 1
    assert body["items"][0]["title_original"] == "Symphonic Suite Alpha"

    misses = await client.get(
        "/api/v1/albums", params={"query": "nonexistent-zzz"}, headers=bearer(admin_tokens)
    )
    assert misses.json()["total_count"] == 0


# ---------------------------------------------------------------------------
# Regressions: track-artist role round-trip & log_score bounds
# ---------------------------------------------------------------------------


async def test_track_artist_roles_survive_read_back(
    client: AsyncClient, admin_tokens: dict
) -> None:
    """REGRESSION: roles were silently dropped by the response schema, so
    every edit round-trip reset credits to 'Composer'."""
    payload = minimal_album_payload("Role Roundtrip") | {
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Vocal Track",
                        "artists": [
                            {"name_original": "Singer A", "role": "Performer"},
                            {"name_original": "Writer B", "role": "Lyricist"},
                        ],
                    }
                ],
            }
        ],
    }
    created = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    assert created.status_code == 201, created.text

    detail = await client.get(
        f"/api/v1/albums/{created.json()['album_id']}", headers=bearer(admin_tokens)
    )
    artists = detail.json()["discs"][0]["tracks"][0]["artists"]
    roles = {a["name_original"]: a["role"] for a in artists}
    assert roles == {"Singer A": "Performer", "Writer B": "Lyricist"}


async def test_track_artist_roles_survive_edit_roundtrip(
    client: AsyncClient, admin_tokens: dict
) -> None:
    """Simulates the frontend edit flow: GET detail, resubmit what was read.
    Roles must remain intact after the second save."""
    payload = minimal_album_payload("Edit Roundtrip") | {
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Vocal Track",
                        "artists": [{"name_original": "Singer A", "role": "Performer"}],
                    }
                ],
            }
        ],
    }
    created = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    album_id = created.json()["album_id"]

    detail = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    body = detail.json()

    resubmit = payload | {
        "album_id": album_id,
        "discs": [
            {
                "disc_number": d["disc_number"],
                "media_type": d["media_type"],
                "container_format": d["container_format"],
                "tracks": [
                    {
                        "track_number": t["track_number"],
                        "title_original": t["title_original"],
                        "artists": [
                            {
                                "name_original": a["name_original"],
                                "name_translated": a["name_translated"],
                                "role": a["role"],  # as the frontend now receives it
                            }
                            for a in t["artists"]
                        ],
                    }
                    for t in d["tracks"]
                ],
            }
            for d in body["discs"]
        ],
    }
    updated = await client.post("/api/v1/albums", json=resubmit, headers=bearer(admin_tokens))
    assert updated.status_code == 201, updated.text

    after = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    role = after.json()["discs"][0]["tracks"][0]["artists"][0]["role"]
    assert role == "Performer"


async def test_negative_log_score_accepted(client: AsyncClient, admin_tokens: dict) -> None:
    """Rip log scores have no lower bound (penalty points can go below zero)."""
    payload = minimal_album_payload("Bad Rip") | {
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "log_type": "EAC",
                "log_score": -412,
                "tracks": [{"track_number": 1, "title_original": "T1"}],
            }
        ],
    }
    created = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    assert created.status_code == 201, created.text

    detail = await client.get(
        f"/api/v1/albums/{created.json()['album_id']}", headers=bearer(admin_tokens)
    )
    assert detail.json()["discs"][0]["log_score"] == -412


async def test_log_score_above_100_rejected(client: AsyncClient, admin_tokens: dict) -> None:
    payload = minimal_album_payload("Too Good") | {
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "log_score": 101,
                "tracks": [{"track_number": 1, "title_original": "T1"}],
            }
        ],
    }
    response = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Regression: changelog captures disc-, track-, and archive-level changes
# ---------------------------------------------------------------------------


async def test_changelog_captures_all_change_layers(
    client: AsyncClient, admin_tokens: dict
) -> None:
    """REGRESSION: the diff engine only tracked album scalars, track titles,
    and archive/link membership — disc fields (log score), track fields
    (duration, bitrate, translations), and credits were invisible."""
    base_disc = {
        "disc_number": 1,
        "media_type": "CD",
        "container_format": "Tracks",
        "log_type": "EAC",
        "log_score": 95,
        "tracks": [
            {
                "track_number": 1,
                "title_original": "Opening",
                "duration_seconds": 200,
                "artists": [{"name_original": "Singer A", "role": "Performer"}],
            }
        ],
    }
    payload = minimal_album_payload("Changelog Coverage") | {"discs": [base_disc]}
    created = await client.post("/api/v1/albums", json=payload, headers=bearer(admin_tokens))
    assert created.status_code == 201, created.text
    album_id = created.json()["album_id"]

    updated_disc = {
        **base_disc,
        "log_score": -100,
        "tracks": [
            {
                "track_number": 1,
                "title_original": "Opening",
                "title_translated": "Opening (EN)",
                "duration_seconds": 245,
                "bitrate_kbps": 1411,
                "bitrate_mode": "CBR",
                "artists": [{"name_original": "Singer A", "role": "Vocalist"}],
            }
        ],
    }
    update_payload = payload | {
        "album_id": album_id,
        "discs": [updated_disc],
        "external_links": [{"site_name": "VGMdb", "url": "https://vgmdb.example/x"}],
    }
    updated = await client.post("/api/v1/albums", json=update_payload, headers=bearer(admin_tokens))
    assert updated.status_code == 201, updated.text

    detail = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(admin_tokens))
    merged_changes: dict = {}
    for changelog in detail.json()["changelogs"]:
        merged_changes.update(changelog["changes"])

    assert merged_changes["Disc 1 · Log Score"] == {
        "type": "updated",
        "old": "95",
        "new": "-100",
    }
    assert merged_changes["D1T1 · Duration"] == {
        "type": "updated",
        "old": "03:20",
        "new": "04:05",
    }
    assert merged_changes["D1T1 · Title (Translated)"] == {
        "type": "added",
        "new": "Opening (EN)",
    }
    assert merged_changes["D1T1 · Bitrate"] == {"type": "added", "new": "1411 kbps CBR"}
    assert merged_changes["D1T1 · Credits"] == {
        "type": "updated",
        "old": "Singer A (Performer)",
        "new": "Singer A (Vocalist)",
    }
    assert merged_changes["External Link (+VGMdb)"]["type"] == "added"
