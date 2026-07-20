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


class TrackIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    track_number: int = Field(..., gt=0, description="Sequential track position index.")
    title_original: str = Field(..., min_length=1, max_length=512)
    title_translated: str | None = Field(default=None, max_length=512)
    duration_seconds: int | None = Field(default=None, ge=0)
    audio_codec: AudioCodec | None = None
    video_codec: VideoCodec | None = None
    bit_depth: int | None = Field(default=None, ge=8, le=32)
    sample_rate: int | None = Field(default=None, ge=8000, le=192000)
    bitrate_kbps: int | None = Field(default=None, ge=8, le=32000)
    bitrate_mode: BitrateMode | None = None


class DiscIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    disc_number: int = Field(default=1, gt=0, description="Physical position index.")
    media_type: MediaType
    container_format: ContainerFormat
    catalog_number: str | None = Field(default=None, max_length=64)
    log_type: LogType | None = None
    log_score: int | None = Field(default=None, description="EAC/XLD precision score mapping.")
    tracks: list[TrackIngestSchema] = Field(..., min_length=1)


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
    links: list[ArchiveLinkIngestSchema] = Field(default_factory=list)


class ExternalLinkIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    site_name: str = Field(..., max_length=128)
    url: str = Field(..., max_length=2048)
    remote_item_id: str | None = Field(default=None, max_length=128)


class CoverIngestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    image_data: bytes = Field(..., description="Base64-encoded image frame buffer string.")
    mime_type: str = Field(default="image/jpeg", max_length=64)
    width: int = Field(default=500, gt=0)
    height: int = Field(default=500, gt=0)


class AlbumIngestRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    title_original: str = Field(..., min_length=1, max_length=512)
    library_category: LibraryCategory
    original_folder_name: str = Field(..., min_length=1, max_length=1024)
    title_translated: str | None = Field(default=None, max_length=512)
    release_date: date | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    discs: list[DiscIngestSchema] = Field(default_factory=list)
    archives: list[ArchiveIngestSchema] = Field(default_factory=list)
    external_links: list[ExternalLinkIngestSchema] = Field(default_factory=list)
    cover: CoverIngestSchema | None = None


class AlbumIngestResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    album_id: uuid.UUID
    title_original: str
    total_discs: int
    total_tracks: int


# --- Read/Query Schemas ---


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
    links: list[ArchiveLinkResponseSchema]


class ExternalLinkResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    site_name: str
    url: str
    remote_item_id: str | None


class AlbumSummaryResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    title_original: str
    title_translated: str | None
    release_date: date | None
    library_category: LibraryCategory
    original_folder_name: str
    total_discs: int
    has_cover: bool


class AlbumDetailResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    title_original: str
    title_translated: str | None
    release_date: date | None
    library_category: LibraryCategory
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
