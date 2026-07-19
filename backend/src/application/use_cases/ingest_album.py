import uuid
from dataclasses import dataclass, field
from datetime import date

from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import (
    Album,
    AlbumArchive,
    AlbumCover,
    ArchiveLink,
    Disc,
    ExternalLink,
    Track,
)
from src.domain.value_objects.music_types import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LibraryCategory,
    LogType,
    MediaType,
    VideoCodec,
)


@dataclass(frozen=True, slots=True)
class TrackIngestDTO:
    track_number: int
    title_original: str
    title_translated: str | None = None
    duration_seconds: int | None = None
    audio_codec: AudioCodec | None = None
    video_codec: VideoCodec | None = None
    bit_depth: int | None = None
    sample_rate: int | None = None
    bitrate_kbps: int | None = None
    bitrate_mode: BitrateMode | None = None


@dataclass(frozen=True, slots=True)
class DiscIngestDTO:
    disc_number: int
    media_type: MediaType
    container_format: ContainerFormat
    catalog_number: str | None = None
    log_type: LogType | None = None
    log_score: int | None = None
    tracks: list[TrackIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ArchiveLinkIngestDTO:
    provider_name: str
    download_url: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ArchiveIngestDTO:
    archive_name: str
    encryption_password: str
    file_size_bytes: int | None = None
    links: list[ArchiveLinkIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ExternalLinkIngestDTO:
    site_name: str
    url: str
    remote_item_id: str | None = None


@dataclass(frozen=True, slots=True)
class CoverIngestDTO:
    image_data: bytes
    mime_type: str = "image/jpeg"
    width: int = 500
    height: int = 500


@dataclass(frozen=True, slots=True)
class IngestAlbumRequest:
    title_original: str
    library_category: LibraryCategory
    original_folder_name: str
    title_translated: str | None = None
    release_date: date | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    discs: list[DiscIngestDTO] = field(default_factory=list)
    archives: list[ArchiveIngestDTO] = field(default_factory=list)
    external_links: list[ExternalLinkIngestDTO] = field(default_factory=list)
    cover: CoverIngestDTO | None = None


@dataclass(frozen=True, slots=True)
class IngestAlbumResponse:
    album_id: uuid.UUID
    title_original: str
    total_discs: int
    total_tracks: int


class IngestAlbumUseCase:
    def __init__(self, album_repo: AlbumRepository) -> None:
        self._album_repo = album_repo

    async def execute(self, request: IngestAlbumRequest) -> IngestAlbumResponse:
        album_id = uuid.uuid4()
        total_tracks_counter = 0

        # 1. Reconstruct nested media disc sub-graphs
        domain_discs: list[Disc] = []
        for disc_dto in request.discs:
            disc_id = uuid.uuid4()
            domain_tracks: list[Track] = []

            for track_dto in disc_dto.tracks:
                total_tracks_counter += 1
                domain_tracks.append(
                    Track(
                        id=uuid.uuid4(),
                        disc_id=disc_id,
                        track_number=track_dto.track_number,
                        title_original=track_dto.title_original,
                        title_translated=track_dto.title_translated,
                        duration_seconds=track_dto.duration_seconds,
                        audio_codec=track_dto.audio_codec,
                        video_codec=track_dto.video_codec,
                        bit_depth=track_dto.bit_depth,
                        sample_rate=track_dto.sample_rate,
                        bitrate_kbps=track_dto.bitrate_kbps,
                        bitrate_mode=track_dto.bitrate_mode,
                    )
                )

            domain_discs.append(
                Disc(
                    id=disc_id,
                    album_id=album_id,
                    disc_number=disc_dto.disc_number,
                    catalog_number=disc_dto.catalog_number,
                    media_type=disc_dto.media_type,
                    container_format=disc_dto.container_format,
                    log_type=disc_dto.log_type,
                    log_score=disc_dto.log_score,
                    tracks=domain_tracks,
                )
            )

        # 2. Map distributed cloud mirror archives
        domain_archives: list[AlbumArchive] = []
        for archive_dto in request.archives:
            archive_id = uuid.uuid4()
            domain_links = [
                ArchiveLink(
                    id=uuid.uuid4(),
                    archive_id=archive_id,
                    provider_name=link_dto.provider_name,
                    download_url=link_dto.download_url,
                    is_active=link_dto.is_active,
                )
                for link_dto in archive_dto.links
            ]
            domain_archives.append(
                AlbumArchive(
                    id=archive_id,
                    album_id=album_id,
                    archive_name=archive_dto.archive_name,
                    encryption_password=archive_dto.encryption_password,
                    file_size_bytes=archive_dto.file_size_bytes,
                    links=domain_links,
                )
            )

        # 3. Map cross-referenced metadata pointers
        domain_external_links = [
            ExternalLink(
                id=uuid.uuid4(),
                album_id=album_id,
                site_name=link_dto.site_name,
                url=link_dto.url,
                remote_item_id=link_dto.remote_item_id,
            )
            for link_dto in request.external_links
        ]

        # 4. Map binary cover art preview frames
        domain_cover = None
        if request.cover:
            domain_cover = AlbumCover(
                id=uuid.uuid4(),
                album_id=album_id,
                image_data=request.cover.image_data,
                mime_type=request.cover.mime_type,
                width=request.cover.width,
                height=request.cover.height,
            )

        # 5. Assemble and persist the unified Aggregate Root node
        album_aggregate = Album(
            id=album_id,
            title_original=request.title_original,
            title_translated=request.title_translated,
            release_date=request.release_date,
            event_id=request.event_id,
            franchise_id=request.franchise_id,
            library_category=request.library_category,
            original_folder_name=request.original_folder_name,
            discs=domain_discs,
            archives=domain_archives,
            external_links=domain_external_links,
            cover=domain_cover,
        )

        await self._album_repo.save(album_aggregate)

        return IngestAlbumResponse(
            album_id=album_id,
            title_original=album_aggregate.title_original,
            total_discs=len(domain_discs),
            total_tracks=total_tracks_counter,
        )