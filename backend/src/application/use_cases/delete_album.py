import uuid
from dataclasses import dataclass

from src.application.exceptions import AlbumNotFoundError
from src.application.repositories.album import AlbumRepository


__all__ = ["AlbumNotFoundError", "DeleteAlbumRequest", "DeleteAlbumUseCase"]


@dataclass(frozen=True, slots=True)
class DeleteAlbumRequest:
    album_id: uuid.UUID


class DeleteAlbumUseCase:
    def __init__(self, album_repo: AlbumRepository) -> None:
        self._album_repo = album_repo

    async def execute(self, request: DeleteAlbumRequest) -> None:
        deleted = await self._album_repo.delete(request.album_id)
        if not deleted:
            raise AlbumNotFoundError("Album not found.")
