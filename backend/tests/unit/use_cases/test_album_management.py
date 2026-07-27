import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.repositories.album import AlbumRepository
from src.application.use_cases.delete_album import (
    AlbumNotFoundError,
    DeleteAlbumRequest,
    DeleteAlbumUseCase,
)
from src.application.use_cases.list_albums import ListAlbumsRequest, ListAlbumsUseCase
from src.domain.entities.music import Album


@pytest.mark.asyncio
async def test_list_albums_queries_repository_and_returns_paginated_response() -> None:
    mock_album_repo = MagicMock(spec=AlbumRepository)
    fake_album = Album(
        id=uuid.uuid4(),
        title_original="Touhou Project OST",
        title_translated=None,
        release_year=2004,
        release_month=8,
        release_day=15,
        event_id=None,
        franchise_id=None,
        original_folder_name="Touhou_OST",
    )
    mock_album_repo.search = AsyncMock(return_value=([fake_album], 1))

    use_case = ListAlbumsUseCase(mock_album_repo)
    request = ListAlbumsRequest(query="Touhou", limit=10, offset=0)

    response = await use_case.execute(request)

    assert response.total_count == 1
    assert len(response.items) == 1
    assert response.items[0].title_original == "Touhou Project OST"
    mock_album_repo.search.assert_awaited_once_with(query="Touhou", limit=10, offset=0)


@pytest.mark.asyncio
async def test_delete_album_raises_not_found_exception() -> None:
    mock_album_repo = MagicMock(spec=AlbumRepository)
    mock_album_repo.delete = AsyncMock(return_value=False)

    use_case = DeleteAlbumUseCase(mock_album_repo)
    album_id = uuid.uuid4()

    with pytest.raises(AlbumNotFoundError):
        await use_case.execute(DeleteAlbumRequest(album_id=album_id))

    mock_album_repo.delete.assert_awaited_once_with(album_id)
