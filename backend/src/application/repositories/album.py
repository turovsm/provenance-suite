import uuid
from abc import ABC, abstractmethod

from src.domain.entities.music import Album


class AlbumRepository(ABC):
    @abstractmethod
    async def save(
        self,
        album: Album,
        user_id: uuid.UUID | None = None,
        album_artist_aliases: list[str] | None = None,
        franchise_aliases: list[str] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, album_id: uuid.UUID) -> Album | None:
        pass

    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Album], int]:
        pass

    @abstractmethod
    async def delete(self, album_id: uuid.UUID) -> bool:
        pass
