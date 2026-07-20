import uuid
from dataclasses import dataclass

from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import Album
from src.domain.value_objects.music_types import LibraryCategory


@dataclass(frozen=True, slots=True)
class ListAlbumsRequest:
    category: LibraryCategory | None = None
    query: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True, slots=True)
class ListAlbumsResponse:
    items: list[Album]
    total_count: int
    limit: int
    offset: int


class ListAlbumsUseCase:
    def __init__(self, album_repo: AlbumRepository) -> None:
        self._album_repo = album_repo

    async def execute(self, request: ListAlbumsRequest) -> ListAlbumsResponse:
        items, total_count = await self._album_repo.search(
            category=request.category,
            query=request.query,
            limit=request.limit,
            offset=request.offset,
        )
        return ListAlbumsResponse(
            items=items,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
        )


@dataclass(frozen=True, slots=True)
class GetAlbumDetailRequest:
    album_id: uuid.UUID


class GetAlbumDetailUseCase:
    def __init__(self, album_repo: AlbumRepository) -> None:
        self._album_repo = album_repo

    async def execute(self, request: GetAlbumDetailRequest) -> Album | None:
        return await self._album_repo.find_by_id(request.album_id)
