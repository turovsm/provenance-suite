import uuid
from abc import ABC, abstractmethod

from src.domain.entities.music import Album
from src.domain.value_objects.music_types import LibraryCategory


class AlbumRepository(ABC):
    @abstractmethod
    async def save(self, album: Album) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, album_id: uuid.UUID) -> Album | None:
        pass

    @abstractmethod
    async def find_by_category(
        self, category: LibraryCategory, limit: int = 50, offset: int = 0
    ) -> list[Album]:
        pass

    @abstractmethod
    async def search(
        self,
        category: LibraryCategory | None = None,
        query: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Album], int]:
        pass

    @abstractmethod
    async def delete(self, album_id: uuid.UUID) -> bool:
        pass
