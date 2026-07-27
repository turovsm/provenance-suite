from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.repositories.album import AlbumRepository
from src.application.use_cases.ingest_album import (
    DiscIngestDTO,
    IngestAlbumRequest,
    IngestAlbumUseCase,
    TrackIngestDTO,
)
from src.domain.value_objects.music_types import (
    AudioCodec,
    ContainerFormat,
    MediaType,
)


@pytest.mark.asyncio
async def test_album_ingest_constructs_valid_aggregate_graph() -> None:
    mock_album_repo = MagicMock(spec=AlbumRepository)
    mock_album_repo.save = AsyncMock()

    use_case = IngestAlbumUseCase(mock_album_repo)

    request = IngestAlbumRequest(
        title_original="Symphony No. 5",
        original_folder_name="Beethoven_Symphony_5",
        title_translated="Symphony No. 5 English Edition",
        release_year=1808,
        discs=[
            DiscIngestDTO(
                disc_number=1,
                media_type=MediaType.CD,
                container_format=ContainerFormat.TRACKS,
                tracks=[
                    TrackIngestDTO(
                        track_number=1,
                        title_original="Allegro con brio",
                        audio_codec=AudioCodec.FLAC,
                        bit_depth=16,
                        sample_rate=44100,
                    )
                ],
            )
        ],
    )

    response = await use_case.execute(request)

    assert response.title_original == "Symphony No. 5"
    assert response.total_discs == 1
    assert response.total_tracks == 1

    mock_album_repo.save.assert_called_once()
    saved_album = mock_album_repo.save.call_args[0][0]
    assert saved_album.title_translated == "Symphony No. 5 English Edition"
    assert saved_album.release_year == 1808
    assert len(saved_album.discs) == 1
    assert saved_album.discs[0].tracks[0].title_original == "Allegro con brio"