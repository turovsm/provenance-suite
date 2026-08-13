from httpx import AsyncClient

from tests.integration.api.conftest import bearer


async def test_unified_entity_directory_filtering(
    client: AsyncClient, user_tokens: dict, admin_tokens: dict
) -> None:
    await client.post(
        "/api/v1/entities/artists",
        json={"name_original": "Test Artist Alpha"},
        headers=bearer(admin_tokens),
    )
    await client.post(
        "/api/v1/entities/franchises",
        json={"name_original": "Test Franchise Beta"},
        headers=bearer(admin_tokens),
    )
    await client.post(
        "/api/v1/entities/labels",
        json={"name_original": "Test Label Gamma"},
        headers=bearer(admin_tokens),
    )
    await client.post(
        "/api/v1/entities/publishers",
        json={"name_original": "Test Publisher Delta"},
        headers=bearer(admin_tokens),
    )

    all_res = await client.get("/api/v1/entities?type=all", headers=bearer(user_tokens))
    assert all_res.status_code == 200
    body = all_res.json()
    assert body["total_count"] == 4

    art_res = await client.get("/api/v1/entities?type=artist", headers=bearer(user_tokens))
    assert art_res.status_code == 200
    assert art_res.json()["total_count"] == 1
    assert art_res.json()["items"][0]["name_original"] == "Test Artist Alpha"


async def test_artist_discography_main_and_contributions(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    art_res = await client.post(
        "/api/v1/entities/artists",
        json={"name_original": "Main Composer"},
        headers=bearer(admin_tokens),
    )
    artist_id = art_res.json()["id"]

    main_album_payload = {
        "title_original": "Main Work",
        "original_folder_name": "Main_Work",
        "album_artist_id": artist_id,
    }
    await client.post("/api/v1/albums", json=main_album_payload, headers=bearer(admin_tokens))

    other_artist_res = await client.post(
        "/api/v1/entities/artists",
        json={"name_original": "Other Artist"},
        headers=bearer(admin_tokens),
    )
    other_artist_id = other_artist_res.json()["id"]

    contrib_album_payload = {
        "title_original": "Compilation Album",
        "original_folder_name": "Compilation_Album",
        "album_artist_id": other_artist_id,
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Remix Track",
                        "artists": [{"name_original": "Main Composer", "role": "Arranger"}],
                    }
                ],
            }
        ],
    }
    await client.post("/api/v1/albums", json=contrib_album_payload, headers=bearer(admin_tokens))

    disco_res = await client.get(
        f"/api/v1/entities/artists/{artist_id}/discography", headers=bearer(user_tokens)
    )
    assert disco_res.status_code == 200
    disco_body = disco_res.json()

    assert len(disco_body["main_albums"]) == 1
    assert disco_body["main_albums"][0]["title_original"] == "Main Work"

    assert len(disco_body["contribution_albums"]) == 1
    assert disco_body["contribution_albums"][0]["title_original"] == "Compilation Album"


async def test_label_and_publisher_auto_creation_during_album_ingest(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    ingest_payload = {
        "title_original": "Auto Entity Ingest",
        "original_folder_name": "Auto_Entity_Ingest",
        "label": "Custom Independent Label",
        "publisher": "Custom Independent Publisher",
    }
    res = await client.post("/api/v1/albums", json=ingest_payload, headers=bearer(admin_tokens))
    assert res.status_code == 201

    labels_res = await client.get(
        "/api/v1/entities/labels?query=Custom", headers=bearer(user_tokens)
    )
    assert labels_res.status_code == 200
    assert len(labels_res.json()) == 1
    assert labels_res.json()[0]["name_original"] == "Custom Independent Label"

    pubs_res = await client.get(
        "/api/v1/entities/publishers?query=Custom", headers=bearer(user_tokens)
    )
    assert pubs_res.status_code == 200
    assert len(pubs_res.json()) == 1
    assert pubs_res.json()[0]["name_original"] == "Custom Independent Publisher"
