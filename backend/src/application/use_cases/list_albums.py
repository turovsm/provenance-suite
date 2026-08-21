import uuid
from dataclasses import dataclass

from src.application.exceptions import AlbumNotFoundError
from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import Album


@dataclass(frozen=True, slots=True)
class ListAlbumsRequest:
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

    async def execute(self, request: GetAlbumDetailRequest) -> Album:
        album = await self._album_repo.find_by_id(request.album_id)
        if album is None:
            raise AlbumNotFoundError("Album not found.")
        return album
