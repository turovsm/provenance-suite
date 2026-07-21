import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

from src.domain.value_objects.music_types import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LibraryCategory,
    LogType,
    MediaType,
    VideoCodec,
)


@dataclass(slots=True)
class Event:
    id: uuid.UUID
    short_name: str
    full_name: str | None
    event_type: str


@dataclass(slots=True)
class Franchise:
    id: uuid.UUID
    name_original: str
    name_translated: str | None
    franchise_type: str


@dataclass(slots=True)
class Artist:
    id: uuid.UUID
    name_original: str
    name_translated: str | None
    is_circle: bool


@dataclass(slots=True)
class AlbumArtist:
    album_id: uuid.UUID
    artist_id: uuid.UUID
    role: str


@dataclass(slots=True)
class TrackArtist:
    track_id: uuid.UUID
    artist_id: uuid.UUID
    role: str


@dataclass(slots=True)
class Track:
    id: uuid.UUID
    disc_id: uuid.UUID
    track_number: int
    title_original: str
    title_translated: str | None
    duration_seconds: int | None
    audio_codec: AudioCodec | None
    video_codec: VideoCodec | None
    bit_depth: int | None
    sample_rate: int | None
    bitrate_kbps: int | None
    bitrate_mode: BitrateMode | None
    artists: list[Artist] = field(default_factory=list)


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
    tracks: list[Track] = field(default_factory=list)


@dataclass(slots=True)
class AlbumCover:
    id: uuid.UUID
    album_id: uuid.UUID
    storage_path: str
    mime_type: str
    width: int
    height: int


@dataclass(slots=True)
class ArchiveLink:
    id: uuid.UUID
    archive_id: uuid.UUID
    provider_name: str
    download_url: str
    is_active: bool


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
    remote_item_id: str | None


@dataclass(slots=True)
class Album:
    id: uuid.UUID
    title_original: str
    title_translated: str | None
    release_date: date | None
    label: str | None = None
    publisher: str | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    categories: list[LibraryCategory] = field(default_factory=list)
    storage_drive: str | None = None
    relative_path: str | None = None
    original_folder_name: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    discs: list[Disc] = field(default_factory=list)
    artists: list[Artist] = field(default_factory=list)
    archives: list[AlbumArchive] = field(default_factory=list)
    external_links: list[ExternalLink] = field(default_factory=list)
    cover: AlbumCover | None = None
