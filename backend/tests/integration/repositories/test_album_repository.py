import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.music import Album, AlbumCover, Disc, Track
from src.domain.value_objects.music_types import (
    AudioCodec,
    ContainerFormat,
    MediaType,
)
from src.infrastructure.db.repositories.album import SqlAlchemyAlbumRepository


@pytest.mark.asyncio
async def test_album_repository_cascading_save_and_hydration(db_session: AsyncSession) -> None:
    repository = SqlAlchemyAlbumRepository(db_session)

    album_id = uuid.uuid4()
    disc_id = uuid.uuid4()
    track_id = uuid.uuid4()
    cover_id = uuid.uuid4()

    track_entity = Track(
        id=track_id,
        disc_id=disc_id,
        track_number=1,
        title_original="Core Stream Node",
        aliases=["CSN", "コア・ストリーム・ノード"],
        duration_seconds=240,
        audio_codec=AudioCodec.FLAC,
        video_codec=None,
        bit_depth=24,
        sample_rate=96000,
        bitrate_kbps=None,
        bitrate_mode=None,
        is_instrumental=False,
    )

    disc_entity = Disc(
        id=disc_id,
        album_id=album_id,
        disc_number=1,
        catalog_number="VAULT-001",
        media_type=MediaType.CD,
        container_format=ContainerFormat.TRACKS,
        log_type=None,
        log_score=None,
        raw_log_text="Sample EAC Log File Content",
        raw_cue_text=None,
        accuraterip_summary="12/12 tracks accurate",
        tracks=[track_entity],
    )

    cover_entity = AlbumCover(
        id=cover_id,
        album_id=album_id,
        storage_path="covers/fake_uuid.jpg",
        cover_type="Front",
    )

    album_aggregate = Album(
        id=album_id,
        title_original="Relational Ledger Matrix",
        aliases=["RLM", "リレーショナル・レジャー・マトリックス"],
        release_year=2026,
        release_month=7,
        release_day=18,
        event_id=None,
        franchise_id=None,
        original_folder_name="RLM_2026_Archival",
        discs=[disc_entity],
        covers=[cover_entity],
    )

    await repository.save(album_aggregate)
    await db_session.flush()

    db_session.expunge_all()

    loaded_aggregate = await repository.find_by_id(album_id)

    assert loaded_aggregate is not None
    assert loaded_aggregate.title_original == "Relational Ledger Matrix"
    assert loaded_aggregate.aliases == ["RLM", "リレーショナル・レジャー・マトリックス"]
    assert loaded_aggregate.release_year == 2026
    assert len(loaded_aggregate.covers) == 1
    assert loaded_aggregate.covers[0].storage_path == "covers/fake_uuid.jpg"

    assert len(loaded_aggregate.discs) == 1
    assert loaded_aggregate.discs[0].catalog_number == "VAULT-001"
    assert loaded_aggregate.discs[0].raw_log_text == "Sample EAC Log File Content"
    assert len(loaded_aggregate.discs[0].tracks) == 1
    assert loaded_aggregate.discs[0].tracks[0].title_original == "Core Stream Node"
    assert loaded_aggregate.discs[0].tracks[0].aliases == ["CSN", "コア・ストリーム・ノード"]
    assert loaded_aggregate.discs[0].tracks[0].sample_rate == 96000
    assert len(loaded_aggregate.changelogs) == 1
