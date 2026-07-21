import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.domain import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LibraryCategory,
    LogType,
    MediaType,
    VideoCodec,
)


# --- Inbound Ingestion Schemas ---


class TrackIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    track_number: int = Field(..., ge=1)
    title_original: str = Field(..., max_length=512)
    title_translated: str | None = Field(default=None, max_length=512)
    duration_seconds: int | None = Field(default=None, ge=0)
    audio_codec: AudioCodec | None = None
    video_codec: VideoCodec | None = None
    bit_depth: int | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=0)
    bitrate_kbps: int | None = Field(default=None, ge=0)
    bitrate_mode: BitrateMode | None = None


class DiscIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    disc_number: int = Field(..., ge=1)
    media_type: MediaType
    container_format: ContainerFormat
    catalog_number: str | None = Field(default=None, max_length=64)
    log_type: LogType | None = None
    log_score: int | None = Field(default=None, ge=0, le=100)
    tracks: list[TrackIngestSchema] = Field(default_factory=list)


class ArchiveLinkIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider_name: str = Field(..., max_length=128)
    download_url: str = Field(..., max_length=2048)
    is_active: bool = True


class ArchiveIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    archive_name: str = Field(..., max_length=512)
    encryption_password: str = Field(..., max_length=512)
    file_size_bytes: int | None = Field(default=None, ge=0)
    hash_sha256: str | None = Field(default=None, max_length=64)
    links: list[ArchiveLinkIngestSchema] = Field(default_factory=list)


class ExternalLinkIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    site_name: str = Field(..., max_length=128)
    url: str = Field(..., max_length=2048)
    remote_item_id: str | None = Field(default=None, max_length=128)


class CoverIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    image_data: bytes  # Pydantic automatically decodes inbound base64 string buffers to bytes
    mime_type: str = "image/jpeg"
    width: int = 500
    height: int = 500


class AlbumIngestRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    title_original: str = Field(..., max_length=512)
    categories: list[LibraryCategory] = Field(..., min_length=1)
    original_folder_name: str = Field(..., max_length=1024)
    title_translated: str | None = Field(default=None, max_length=512)
    release_date: date | None = None
    label: str | None = Field(default=None, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    storage_drive: str | None = Field(default=None, max_length=64)
    relative_path: str | None = Field(default=None, max_length=1024)
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    discs: list[DiscIngestSchema] = Field(default_factory=list)
    archives: list[ArchiveIngestSchema] = Field(default_factory=list)
    external_links: list[ExternalLinkIngestSchema] = Field(default_factory=list)
    cover: CoverIngestSchema | None = None


# --- Outbound Response Outflow Schemas ---


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
    title_translated: str | None
    release_date: date | None
    label: str | None
    publisher: str | None
    categories: list[LibraryCategory]
    original_folder_name: str
    total_discs: int
    has_cover: bool


class TrackResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: uuid.UUID
    track_number: int
    title_original: str
    title_translated: str | None
    duration_seconds: int | None
    audio_codec: AudioCodec | None
    bit_depth: int | None
    sample_rate: int | None


class DiscResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: uuid.UUID
    disc_number: int
    catalog_number: str | None
    media_type: MediaType
    container_format: ContainerFormat
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
    remote_item_id: str | None


class AlbumDetailResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: uuid.UUID
    title_original: str
    title_translated: str | None
    release_date: date | None
    label: str | None
    publisher: str | None
    categories: list[LibraryCategory]
    original_folder_name: str
    discs: list[DiscResponseSchema]
    archives: list[ArchiveResponseSchema]
    external_links: list[ExternalLinkResponseSchema]
    has_cover: bool


class PaginatedAlbumsResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    items: list[AlbumSummaryResponseSchema]
    total_count: int
    limit: int
    offset: int
