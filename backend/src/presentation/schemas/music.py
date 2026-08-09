import uuid
from datetime import datetime
from typing import Any

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field

from src.domain import (
    MAX_ALIAS_LENGTH,
    MAX_ALIASES_PER_ENTITY,
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LogType,
    MediaType,
    VideoCodec,
)
from src.presentation.schemas.entities import ArtistResponseSchema


class ArtistIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID | None = None
    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    role: str = Field(default="Primary", max_length=64)


class TrackIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    track_number: int = Field(..., ge=1)
    title_original: str = Field(..., max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    duration_seconds: int | None = Field(default=None, ge=0)
    audio_codec: AudioCodec | None = None
    video_codec: VideoCodec | None = None
    bit_depth: int | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=0)
    bitrate_kbps: int | None = Field(default=None, ge=0)
    bitrate_mode: BitrateMode | None = None
    is_instrumental: bool = Field(default=False)
    artists: list[ArtistIngestSchema] = Field(default_factory=list)


class DiscIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    disc_number: int = Field(..., ge=1)
    media_type: MediaType
    container_format: ContainerFormat
    catalog_number: str | None = Field(default=None, max_length=64)
    log_type: LogType | None = None
    log_score: int | None = Field(default=None, le=100)
    raw_log_text: str | None = None
    raw_cue_text: str | None = None
    accuraterip_summary: str | None = None
    tracks: list[TrackIngestSchema] = Field(default_factory=list)


class ArchiveLinkIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider_name: str = Field(..., max_length=128)
    download_url: str = Field(..., max_length=2048)
    is_active: bool = True


class ArchiveIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    archive_name: str = Field(..., max_length=512)
    encryption_password: str = Field(default="", max_length=512)
    file_size_bytes: int | None = Field(default=None, ge=0)
    hash_sha256: str | None = Field(default=None, max_length=64)
    links: list[ArchiveLinkIngestSchema] = Field(default_factory=list)


class ExternalLinkIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_name: str = Field(..., max_length=128)
    url: str = Field(..., max_length=2048)


class CoverIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_data: Base64Bytes
    cover_type: str = Field(default="Front", max_length=64)


class AlbumIngestRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    album_id: uuid.UUID | None = None
    title_original: str = Field(..., max_length=MAX_ALIAS_LENGTH)
    original_folder_name: str = Field(..., max_length=1024)
    aliases: list[str] = Field(
        default_factory=list,
        max_length=MAX_ALIASES_PER_ENTITY,
        description=(
            "All non-official title variants: acronyms, romaji, translated titles, "
            "regional release titles, etc."
        ),
    )
    release_year: int | None = Field(default=None, ge=1800, le=2100)
    release_month: int | None = Field(default=None, ge=1, le=12)
    release_day: int | None = Field(default=None, ge=1, le=31)
    label: str | None = Field(default=None, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    storage_drive: str | None = Field(default=None, max_length=64)
    relative_path: str | None = Field(default=None, max_length=1024)
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    album_artist_id: uuid.UUID | None = None
    album_artist: ArtistIngestSchema | None = None
    discs: list[DiscIngestSchema] = Field(default_factory=list)
    covers: list[CoverIngestSchema] = Field(default_factory=list)
    archives: list[ArchiveIngestSchema] = Field(default_factory=list)
    external_links: list[ExternalLinkIngestSchema] = Field(default_factory=list)


class CoverResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    storage_path: str
    thumbhash: str | None
    url: str
    cover_type: str
    created_at: datetime | None


class AlbumIngestResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    album_id: uuid.UUID
    title_original: str
    total_discs: int
    total_tracks: int


class AlbumSummaryResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    title_original: str
    aliases: list[str] = Field(default_factory=list)
    release_year: int | None
    release_month: int | None
    release_day: int | None
    label: str | None
    publisher: str | None
    original_folder_name: str
    album_artist: ArtistResponseSchema | None
    total_discs: int
    covers: list[CoverResponseSchema]


class TrackArtistResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    role: str


class TrackResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    track_number: int
    title_original: str
    aliases: list[str] = Field(default_factory=list)
    duration_seconds: int | None
    audio_codec: AudioCodec | None
    video_codec: VideoCodec | None = None
    bit_depth: int | None
    sample_rate: int | None
    bitrate_kbps: int | None = None
    bitrate_mode: BitrateMode | None = None
    is_instrumental: bool
    artists: list[TrackArtistResponseSchema] = Field(default_factory=list)


class DiscResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    disc_number: int
    catalog_number: str | None
    media_type: MediaType
    container_format: ContainerFormat
    log_type: LogType | None
    log_score: int | None
    raw_log_text: str | None
    raw_cue_text: str | None
    accuraterip_summary: str | None
    tracks: list[TrackResponseSchema]


class ArchiveLinkResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    provider_name: str
    download_url: str
    is_active: bool


class ArchiveResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    archive_name: str
    encryption_password: str
    file_size_bytes: int | None
    hash_sha256: str | None
    links: list[ArchiveLinkResponseSchema]


class ExternalLinkResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    site_name: str
    url: str


class AlbumChangelogResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    changes: dict[str, Any]
    created_at: datetime | None


class AlbumDetailResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    title_original: str
    aliases: list[str] = Field(default_factory=list)
    release_year: int | None
    release_month: int | None
    release_day: int | None
    label: str | None
    publisher: str | None
    storage_drive: str | None = None
    relative_path: str | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    original_folder_name: str
    album_artist: ArtistResponseSchema | None
    discs: list[DiscResponseSchema]
    covers: list[CoverResponseSchema]
    archives: list[ArchiveResponseSchema]
    external_links: list[ExternalLinkResponseSchema]
    changelogs: list[AlbumChangelogResponseSchema]


class PaginatedAlbumsResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[AlbumSummaryResponseSchema]
    total_count: int
    limit: int
    offset: int
