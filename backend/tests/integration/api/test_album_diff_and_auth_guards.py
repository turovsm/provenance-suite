import uuid

from httpx import AsyncClient

from tests.integration.api.conftest import bearer


async def test_album_diff_removal_and_technical_modifications(
    client: AsyncClient, admin_tokens: dict, user_tokens: dict
) -> None:
    # 1. Create multi-disc album
    initial_payload = {
        "title_original": "Initial Symphony",
        "original_folder_name": "Init_Symphony",
        "storage_drive": "NAS-01",
        "relative_path": "Music/OST/",
        "release_year": 2020,
        "release_month": 4,
        "release_day": 15,
        "label": "Original Records",
        "publisher": "Original Distribution",
        "discs": [
            {
                "disc_number": 1,
                "media_type": "CD",
                "container_format": "Tracks",
                "catalog_number": "CAT-001",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Track A",
                        "duration_seconds": 180,
                        "audio_codec": "FLAC",
                        "bit_depth": 16,
                        "sample_rate": 44100,
                    },
                    {
                        "track_number": 2,
                        "title_original": "Track B",
                        "duration_seconds": 220,
                        "is_instrumental": False,
                    },
                ],
            },
            {
                "disc_number": 2,
                "media_type": "DVD",
                "container_format": "ISO",
                "tracks": [
                    {"track_number": 1, "title_original": "Video Clip", "video_codec": "H264"}
                ],
            },
        ],
        "archives": [
            {
                "archive_name": "init.7z.001",
                "encryption_password": "pass",
                "file_size_bytes": 500000,
                "hash_sha256": "abc12345",
                "links": [{"provider_name": "Mega", "download_url": "https://mega.nz/file1"}],
            }
        ],
        "external_links": [{"site_name": "VGMdb", "url": "https://vgmdb.net/album/1"}],
    }

    create_res = await client.post(
        "/api/v1/albums", json=initial_payload, headers=bearer(admin_tokens)
    )
    assert create_res.status_code == 201
    album_id = create_res.json()["album_id"]

    # 2. Update the album
    updated_payload = {
        **initial_payload,
        "album_id": album_id,
        "title_original": "Initial Symphony (Updated)",
        "label": "Remaster Label",
        "publisher": None,
        "discs": [
            {
                "disc_number": 1,
                "media_type": "BD",  # Changed media_type
                "container_format": "Tracks",
                "catalog_number": "CAT-001-RE",
                "tracks": [
                    {
                        "track_number": 1,
                        "title_original": "Track A (Remastered)",
                        "duration_seconds": 185,
                        "audio_codec": "FLAC",
                        "bit_depth": 24,  # Changed bit depth
                        "sample_rate": 96000,  # Changed sample rate
                    }
                ],
            }
        ],
        "archives": [],  # Removed archive
        "external_links": [
            {"site_name": "MusicBrainz", "url": "https://musicbrainz.org/release/1"}
        ],
    }

    update_res = await client.post(
        "/api/v1/albums", json=updated_payload, headers=bearer(admin_tokens)
    )
    assert update_res.status_code == 201

    # 3. Verify changelog captures structural removals
    detail_res = await client.get(f"/api/v1/albums/{album_id}", headers=bearer(user_tokens))
    assert detail_res.status_code == 200
    changelogs = detail_res.json()["changelogs"]

    merged_changes = {}
    for cl in changelogs:
        merged_changes.update(cl["changes"])

    # Verifies removal and modification branches in _compute_album_diff
    assert "Disc 2" in merged_changes
    assert merged_changes["Disc 2"]["type"] == "removed"
    assert "D1T2" in merged_changes
    assert merged_changes["D1T2"]["type"] == "removed"
    assert merged_changes["Disc 1 · Media Type"]["new"] == "BD"
    assert merged_changes["D1T1 · Bit Depth"]["new"] == "24"
    assert "Archive Volume (-init.7z.001)" in merged_changes
    assert "External Link (-VGMdb)" in merged_changes
    assert "External Link (+MusicBrainz)" in merged_changes


async def test_auth_guards_and_superuser_rejections(client: AsyncClient, user_tokens: dict) -> None:
    # Test superuser guards with standard user tokens
    assert (
        await client.post(
            "/api/v1/entities/artists", json={"name_original": "X"}, headers=bearer(user_tokens)
        )
    ).status_code == 403
    assert (
        await client.put(
            f"/api/v1/entities/artists/{uuid.uuid4()}",
            json={"name_original": "X"},
            headers=bearer(user_tokens),
        )
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/entities/artists/{uuid.uuid4()}", headers=bearer(user_tokens))
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/entities/events", json={"short_name": "E"}, headers=bearer(user_tokens)
        )
    ).status_code == 403
