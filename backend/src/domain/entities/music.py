import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from src.domain.value_objects.aliases import normalize_aliases
from src.domain.value_objects.music_types import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LogType,
    MediaType,
    VideoCodec,
)


@dataclass(slots=True)
class Event:
    id: uuid.UUID
    short_name: str
    full_name: str | None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "HELD"


@dataclass(slots=True)
class Franchise:
    id: uuid.UUID
    name_original: str
    aliases: list[str] = field(default_factory=list)
    franchise_type: str = "Game"

    def __post_init__(self) -> None:
        self.aliases = normalize_aliases(self.aliases)


@dataclass(slots=True)
class Artist:
    id: uuid.UUID
    name_original: str
    aliases: list[str] = field(default_factory=list)
    role: str = "Primary"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self.aliases = normalize_aliases(self.aliases)


@dataclass(slots=True)
class Track:
    id: uuid.UUID
    disc_id: uuid.UUID
    track_number: int
    title_original: str
    aliases: list[str]
    duration_seconds: int | None
    audio_codec: AudioCodec | None
    video_codec: VideoCodec | None
    bit_depth: int | None
    sample_rate: int | None
    bitrate_kbps: int | None
    bitrate_mode: BitrateMode | None
    is_instrumental: bool = False
    artists: list[Artist] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.aliases = normalize_aliases(self.aliases)


@dataclass(slots=True)
class Disc:
    id: uuid.UUID
    album_id: uuid.UUID
    disc_number: int
    catalog_number: str | None
    media_type: MediaType
    container_format: ContainerFormat
    log_type: LogType | None
    log_score: int | None
    raw_log_text: str | None = None
    raw_cue_text: str | None = None
    accuraterip_summary: str | None = None
    tracks: list[Track] = field(default_factory=list)


@dataclass(slots=True)
class AlbumCover:
    id: uuid.UUID
    album_id: uuid.UUID
    storage_path: str
    thumbhash: str | None = None
    url: str | None = None
    cover_type: str = "Front"
    created_at: datetime | None = None


@dataclass(slots=True)
class ArchiveLink:
    id: uuid.UUID
    archive_id: uuid.UUID
    provider_name: str
    download_url: str
    is_active: bool = True


@dataclass(slots=True)
class AlbumArchive:
    id: uuid.UUID
    album_id: uuid.UUID
    archive_name: str
    encryption_password: str
    file_size_bytes: int | None
    hash_sha256: str | None = None
    links: list[ArchiveLink] = field(default_factory=list)


@dataclass(slots=True)
class ExternalLink:
    id: uuid.UUID
    album_id: uuid.UUID
    site_name: str
    url: str


@dataclass(slots=True)
class AlbumChangelog:
    id: uuid.UUID
    album_id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    changes: dict[str, Any]
    created_at: datetime | None = None


@dataclass(slots=True)
class Album:
    id: uuid.UUID
    title_original: str
    aliases: list[str] = field(default_factory=list)
    release_year: int | None = None
    release_month: int | None = None
    release_day: int | None = None
    release_date_sort: date | None = None
    label: str | None = None
    publisher: str | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    album_artist_id: uuid.UUID | None = None
    album_artist: Artist | None = None
    storage_drive: str | None = None
    relative_path: str | None = None
    original_folder_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    discs: list[Disc] = field(default_factory=list)
    covers: list[AlbumCover] = field(default_factory=list)
    archives: list[AlbumArchive] = field(default_factory=list)
    external_links: list[ExternalLink] = field(default_factory=list)
    changelogs: list[AlbumChangelog] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.aliases = normalize_aliases(self.aliases)
