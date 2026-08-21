from src.domain.entities.music import (
    Album,
    AlbumArchive,
    AlbumChangelog,
    AlbumCover,
    ArchiveLink,
    Artist,
    Disc,
    Event,
    ExternalLink,
    Franchise,
    Track,
)
from src.domain.entities.user import User
from src.domain.exceptions import DomainError, DomainInvariantError, InvalidEmailError
from src.domain.value_objects.aliases import (
    MAX_ALIAS_LENGTH,
    MAX_ALIASES_PER_ENTITY,
    normalize_aliases,
)
from src.domain.value_objects.email import EmailAddress
from src.domain.value_objects.music_types import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LogType,
    MediaType,
    VideoCodec,
)
from src.domain.value_objects.user_role import UserRole


__all__ = [
    "User",
    "UserRole",
    "EmailAddress",
    "DomainError",
    "InvalidEmailError",
    "DomainInvariantError",
    "Event",
    "Franchise",
    "Artist",
    "Album",
    "Disc",
    "Track",
    "AlbumCover",
    "AlbumArchive",
    "ArchiveLink",
    "ExternalLink",
    "AlbumChangelog",
    "MediaType",
    "ContainerFormat",
    "LogType",
    "AudioCodec",
    "VideoCodec",
    "BitrateMode",
    "MAX_ALIASES_PER_ENTITY",
    "MAX_ALIAS_LENGTH",
    "normalize_aliases",
]
