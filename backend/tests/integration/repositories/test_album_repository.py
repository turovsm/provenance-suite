import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.music import Album, AlbumCover, Disc, Track
from src.domain.value_objects.music_types import (
    AudioCodec,
    ContainerFormat,
    LibraryCategory,
    MediaType,
)
from src.infrastructure.db.repositories.album import SqlAlchemyAlbumRepository


@pytest.mark.asyncio
async def test_album_repository_cascading_save_and_hydration(db_session: AsyncSession) -> None:
    """Verifies saving an aggregate root serializes and reloads the entire relational sub-graph."""
    repository = SqlAlchemyAlbumRepository(db_session)
    album_id = uuid.uuid4()
    disc_id = uuid.uuid4()
    track_id = uuid.uuid4()
    cover_id = uuid.uuid4()

    # Hydrate a full domain entity graph loop
    track_entity = Track(
        id=track_id,
        disc_id=disc_id,
        track_number=1,
        title_original="Core Stream Node",
        title_translated=None,
        duration_seconds=240,
        audio_codec=AudioCodec.FLAC,
        video_codec=None,
        bit_depth=24,
        sample_rate=96000,
        bitrate_kbps=None,
        bitrate_mode=None,
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
        tracks=[track_entity],
    )

    cover_entity = AlbumCover(
        id=cover_id,
        album_id=album_id,
        image_data=b"\x00\x01\x02\x03_fake_jpeg_buffer",
        mime_type="image/jpeg",
        width=500,
        height=500,
    )

    album_aggregate = Album(
        id=album_id,
        title_original="Relational Ledger Matrix",
        title_translated="RLM Edition",
        release_date=None,
        event_id=None,
        franchise_id=None,
        library_category=LibraryCategory.ELECTRONIC,
        original_folder_name="RLM_2026_Archival",
        discs=[disc_entity],
        cover=cover_entity,
    )

    # 1. Execute write down to transaction frames
    await repository.save(album_aggregate)
    await db_session.flush()

    # 2. Clear session to completely drop local cache references and guarantee network pull reads
    db_session.expunge_all()

    # 3. Hydra aggregate root block using optimized selectinload configurations
    loaded_aggregate = await repository.find_by_id(album_id)

    assert loaded_aggregate is not None
    assert loaded_aggregate.title_original == "Relational Ledger Matrix"
    assert loaded_aggregate.cover is not None
    assert loaded_aggregate.cover.image_data == b"\x00\x01\x02\x03_fake_jpeg_buffer"

    # Confirm cascading child model mapping preservation
    assert len(loaded_aggregate.discs) == 1
    assert loaded_aggregate.discs[0].catalog_number == "VAULT-001"
    assert len(loaded_aggregate.discs[0].tracks) == 1
    assert loaded_aggregate.discs[0].tracks[0].title_original == "Core Stream Node"
    assert loaded_aggregate.discs[0].tracks[0].sample_rate == 96000
