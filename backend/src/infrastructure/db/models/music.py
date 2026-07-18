import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LibraryCategory,
    LogType,
    MediaType,
    VideoCodec,
)
from src.infrastructure.db.models.base import BaseInfrastructureModel


class EventModel(BaseInfrastructureModel):
    """Doujin events like Comiket, M3, etc."""

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)

    albums: Mapped[list["AlbumModel"]] = relationship("AlbumModel", back_populates="event")


class FranchiseModel(BaseInfrastructureModel):
    """Franchise name, such as game series, movie title, etc."""

    __tablename__ = "franchises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_original: Mapped[str] = mapped_column(String(512), nullable=False)
    name_translated: Mapped[str | None] = mapped_column(String(512), nullable=True)
    franchise_type: Mapped[str] = mapped_column(String(128), nullable=False)

    albums: Mapped[list["AlbumModel"]] = relationship("AlbumModel", back_populates="franchise")


class ArtistModel(BaseInfrastructureModel):
    """Circles, composers, vocalists, and arrangers."""

    __tablename__ = "artists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_original: Mapped[str] = mapped_column(String(512), nullable=False)
    name_translated: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_circle: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    album_associations: Mapped[list["AlbumArtistModel"]] = relationship(
        "AlbumArtistModel", back_populates="artist", cascade="all, delete-orphan"
    )


class AlbumArtistModel(BaseInfrastructureModel):
    """Many-to-Many album artists table."""

    __tablename__ = "album_artists"

    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artists.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(64), default="Primary", primary_key=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="artist_associations")
    artist: Mapped["ArtistModel"] = relationship("ArtistModel", back_populates="album_associations")


class AlbumModel(BaseInfrastructureModel):
    """Welp, albums ig."""

    __tablename__ = "albums"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_original: Mapped[str] = mapped_column(String(512), nullable=False)
    title_translated: Mapped[str | None] = mapped_column(String(512), nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    franchise_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("franchises.id", ondelete="SET NULL"), nullable=True
    )
    library_category: Mapped[LibraryCategory] = mapped_column(
        Enum(LibraryCategory, native_enum=True), nullable=False
    )
    original_folder_name: Mapped[str] = mapped_column(String(1024), nullable=False)

    event: Mapped["EventModel | None"] = relationship("EventModel", back_populates="albums")
    franchise: Mapped["FranchiseModel | None"] = relationship(
        "FranchiseModel", back_populates="albums"
    )
    artist_associations: Mapped[list["AlbumArtistModel"]] = relationship(
        "AlbumArtistModel", back_populates="album", cascade="all, delete-orphan"
    )
    discs: Mapped[list["DiscModel"]] = relationship(
        "DiscModel", back_populates="album", cascade="all, delete-orphan"
    )
    cover: Mapped["AlbumCoverModel | None"] = relationship(
        "AlbumCoverModel", back_populates="album", uselist=False, cascade="all, delete-orphan"
    )
    archives: Mapped[list["AlbumArchiveModel"]] = relationship(
        "AlbumArchiveModel", back_populates="album", cascade="all, delete-orphan"
    )
    external_links: Mapped[list["ExternalLinkModel"]] = relationship(
        "ExternalLinkModel", back_populates="album", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_albums_release_date_desc", release_date.desc()),
        Index("idx_albums_library_category", library_category),
        Index("idx_albums_folder_name", original_folder_name),
    )


class DiscModel(BaseInfrastructureModel):
    """Track individual discs within albums."""

    __tablename__ = "discs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
    disc_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    catalog_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType, native_enum=True), nullable=False)
    container_format: Mapped[ContainerFormat] = mapped_column(
        Enum(ContainerFormat, native_enum=True), nullable=False
    )
    log_type: Mapped[LogType | None] = mapped_column(Enum(LogType, native_enum=True), nullable=True)
    log_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="discs")
    tracks: Mapped[list["TrackModel"]] = relationship(
        "TrackModel", back_populates="disc", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("log_score <= 100", name="chk_valid_log_score"),
        Index("ux_discs_album_number", album_id, disc_number, unique=True),
        Index("idx_discs_catalog_number", catalog_number),
    )


class TrackModel(BaseInfrastructureModel):
    """Track info ig."""

    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discs.id", ondelete="CASCADE"), nullable=False
    )
    track_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_original: Mapped[str] = mapped_column(String(512), nullable=False)
    title_translated: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_codec: Mapped[AudioCodec | None] = mapped_column(
        Enum(AudioCodec, native_enum=True), nullable=True
    )
    video_codec: Mapped[VideoCodec | None] = mapped_column(
        Enum(VideoCodec, native_enum=True), nullable=True
    )
    bit_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitrate_mode: Mapped[BitrateMode | None] = mapped_column(
        Enum(BitrateMode, native_enum=True), nullable=True
    )

    disc: Mapped["DiscModel"] = relationship("DiscModel", back_populates="tracks")

    __table_args__ = (
        CheckConstraint("track_number > 0", name="chk_track_number_positive"),
        Index("ux_tracks_disc_number", disc_id, track_number, unique=True),
    )


class AlbumCoverModel(BaseInfrastructureModel):
    """Cover art preview for albums."""

    __tablename__ = "album_covers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), default="image/jpeg", nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=500, nullable=False)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="cover")


class AlbumArchiveModel(BaseInfrastructureModel):
    """Album archives, could be split into several parts (.7z.001, .7z.002)"""

    __tablename__ = "album_archives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
    archive_name: Mapped[str] = mapped_column(String(512), nullable=False)
    encryption_password: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="archives")
    links: Mapped[list["ArchiveLinkModel"]] = relationship(
        "ArchiveLinkModel", back_populates="archive", cascade="all, delete-orphan"
    )


class ArchiveLinkModel(BaseInfrastructureModel):
    """Download links to cloud services (Mega, GDrive, OneDrive)."""

    __tablename__ = "archive_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("album_archives.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    download_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    archive: Mapped["AlbumArchiveModel"] = relationship("AlbumArchiveModel", back_populates="links")


class ExternalLinkModel(BaseInfrastructureModel):
    """Links to external databases (VGMdb, MusicBrainz)."""

    __tablename__ = "external_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("albums.id", ondelete="CASCADE"), nullable=False
    )
    site_name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    remote_item_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="external_links")
