import uuid
from datetime import date
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.models.base import BaseInfrastructureModel


CASCADE_DELETE_ORPHAN = "all, delete-orphan"
ON_DELETE_SET_NULL = "SET NULL"
ALBUMS_ID_FK = "albums.id"


class EventModel(BaseInfrastructureModel):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_start_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_end_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_date_sort: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    additional_dates: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    status: Mapped[str] = mapped_column(String(32), default="HELD", nullable=False)

    albums: Mapped[list["AlbumModel"]] = relationship("AlbumModel", back_populates="event")


class FranchiseModel(BaseInfrastructureModel):
    __tablename__ = "franchises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_original: Mapped[str] = mapped_column(String(512), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    franchise_type: Mapped[str] = mapped_column(String(128), nullable=False)

    albums: Mapped[list["AlbumModel"]] = relationship("AlbumModel", back_populates="franchise")


class ArtistModel(BaseInfrastructureModel):
    __tablename__ = "artists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_original: Mapped[str] = mapped_column(String(512), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    track_associations: Mapped[list["TrackArtistModel"]] = relationship(
        "TrackArtistModel", back_populates="artist", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )

    __table_args__ = (
        Index(
            "idx_artists_name_orig_trgm",
            name_original,
            postgresql_using="gin",
            postgresql_ops={"name_original": "gin_trgm_ops"},
        ),
    )


class TrackArtistModel(BaseInfrastructureModel):
    __tablename__ = "track_artists"

    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True
    )
    artist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artists.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(64), default="Composer", primary_key=True)

    track: Mapped["TrackModel"] = relationship("TrackModel", back_populates="artist_associations")
    artist: Mapped["ArtistModel"] = relationship("ArtistModel", back_populates="track_associations")


class AlbumModel(BaseInfrastructureModel):
    __tablename__ = "albums"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title_original: Mapped[str] = mapped_column(String(512), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    release_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    release_month: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    release_day: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    release_date_sort: Mapped[date | None] = mapped_column(Date, nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id", ondelete=ON_DELETE_SET_NULL), nullable=True
    )
    franchise_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("franchises.id", ondelete=ON_DELETE_SET_NULL), nullable=True
    )
    album_artist_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artists.id", ondelete=ON_DELETE_SET_NULL), nullable=True
    )
    storage_drive: Mapped[str | None] = mapped_column(String(64), nullable=True)
    relative_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    original_folder_name: Mapped[str] = mapped_column(String(1024), nullable=False)

    event: Mapped["EventModel | None"] = relationship("EventModel", back_populates="albums")
    franchise: Mapped["FranchiseModel | None"] = relationship(
        "FranchiseModel", back_populates="albums"
    )
    album_artist: Mapped["ArtistModel | None"] = relationship("ArtistModel", lazy="selectin")
    discs: Mapped[list["DiscModel"]] = relationship(
        "DiscModel", back_populates="album", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )
    covers: Mapped[list["AlbumCoverModel"]] = relationship(
        "AlbumCoverModel", back_populates="album", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )
    archives: Mapped[list["AlbumArchiveModel"]] = relationship(
        "AlbumArchiveModel", back_populates="album", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )
    external_links: Mapped[list["ExternalLinkModel"]] = relationship(
        "ExternalLinkModel", back_populates="album", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )
    changelogs: Mapped[list["AlbumChangelogModel"]] = relationship(
        "AlbumChangelogModel",
        back_populates="album",
        cascade=CASCADE_DELETE_ORPHAN,
        lazy="selectin",
    )

    __table_args__ = (
        CheckConstraint(
            "release_month >= 1 AND release_month <= 12", name="chk_valid_release_month"
        ),
        CheckConstraint("release_day >= 1 AND release_day <= 31", name="chk_valid_release_day"),
        Index("idx_albums_release_date_sort_desc", release_date_sort.desc()),
        Index(
            "idx_albums_title_orig_trgm",
            title_original,
            postgresql_using="gin",
            postgresql_ops={"title_original": "gin_trgm_ops"},
        ),
        Index(
            "idx_albums_folder_name_trgm",
            original_folder_name,
            postgresql_using="gin",
            postgresql_ops={"original_folder_name": "gin_trgm_ops"},
        ),
    )


class DiscModel(BaseInfrastructureModel):
    __tablename__ = "discs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(ALBUMS_ID_FK, ondelete="CASCADE"), nullable=False
    )
    disc_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    catalog_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    container_format: Mapped[str] = mapped_column(String(64), nullable=False)
    log_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    log_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_log_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_cue_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    accuraterip_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="discs")
    tracks: Mapped[list["TrackModel"]] = relationship(
        "TrackModel", back_populates="disc", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("log_score <= 100", name="chk_valid_log_score"),
        Index("ux_discs_album_number", album_id, disc_number, unique=True),
    )


class TrackModel(BaseInfrastructureModel):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discs.id", ondelete="CASCADE"), nullable=False
    )
    track_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title_original: Mapped[str] = mapped_column(String(512), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    video_codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bit_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitrate_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_instrumental: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    disc: Mapped["DiscModel"] = relationship("DiscModel", back_populates="tracks")
    artist_associations: Mapped[list["TrackArtistModel"]] = relationship(
        "TrackArtistModel", back_populates="track", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("track_number > 0", name="chk_track_number_positive"),
        Index("ux_tracks_disc_number", disc_id, track_number, unique=True),
    )


class AlbumCoverModel(BaseInfrastructureModel):
    __tablename__ = "album_covers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(ALBUMS_ID_FK, ondelete="CASCADE"), nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbhash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cover_type: Mapped[str] = mapped_column(String(64), default="Front", nullable=False)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="covers")


class AlbumArchiveModel(BaseInfrastructureModel):
    __tablename__ = "album_archives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(ALBUMS_ID_FK, ondelete="CASCADE"), nullable=False
    )
    archive_name: Mapped[str] = mapped_column(String(512), nullable=False)
    encryption_password: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    hash_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="archives")
    links: Mapped[list["ArchiveLinkModel"]] = relationship(
        "ArchiveLinkModel", back_populates="archive", cascade=CASCADE_DELETE_ORPHAN, lazy="selectin"
    )


class ArchiveLinkModel(BaseInfrastructureModel):
    __tablename__ = "archive_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("album_archives.id", ondelete="CASCADE"), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    download_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    archive: Mapped["AlbumArchiveModel"] = relationship("AlbumArchiveModel", back_populates="links")


class ExternalLinkModel(BaseInfrastructureModel):
    __tablename__ = "external_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(ALBUMS_ID_FK, ondelete="CASCADE"), nullable=False
    )
    site_name: Mapped[str] = mapped_column(String(128), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="external_links")


class AlbumChangelogModel(BaseInfrastructureModel):
    __tablename__ = "album_changelogs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(ALBUMS_ID_FK, ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete=ON_DELETE_SET_NULL), nullable=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    changes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    album: Mapped["AlbumModel"] = relationship("AlbumModel", back_populates="changelogs")

    __table_args__ = (
        Index("idx_album_changelogs_album_id", album_id),
        Index("idx_album_changelogs_user_id", user_id),
    )


ALIASES_TRGM_INDEX_DDL: tuple[tuple[str, str], ...] = (
    ("albums", "idx_albums_aliases_trgm"),
    ("artists", "idx_artists_aliases_trgm"),
    ("franchises", "idx_franchises_aliases_trgm"),
)


@event.listens_for(BaseInfrastructureModel.metadata, "after_create")
def _create_aliases_trgm_indexes(target, connection, **kw) -> None:
    for table_name, index_name in ALIASES_TRGM_INDEX_DDL:
        connection.execute(
            text(
                f"CREATE INDEX IF NOT EXISTS {index_name} "
                f"ON {table_name} USING gin ((aliases::text) gin_trgm_ops)"
            )
        )


@event.listens_for(BaseInfrastructureModel.metadata, "before_drop")
def _drop_aliases_trgm_indexes(_target, connection, **_kw) -> None:
    for _table_name, index_name in ALIASES_TRGM_INDEX_DDL:
        connection.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
