import uuid
from dataclasses import dataclass, field

from src.application.repositories.album import AlbumRepository
from src.domain.entities.music import (
    Album,
    AlbumArchive,
    AlbumCover,
    ArchiveLink,
    Artist,
    Disc,
    ExternalLink,
    Track,
)
from src.domain.value_objects.music_types import (
    AudioCodec,
    BitrateMode,
    ContainerFormat,
    LogType,
    MediaType,
    VideoCodec,
)
from src.infrastructure.storage.object_storage import MinioObjectStorageService


@dataclass(frozen=True, slots=True)
class ArtistIngestDTO:
    name_original: str
    id: uuid.UUID | None = None
    name_translated: str | None = None
    role: str = "Primary"


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
    is_instrumental: bool = False
    artists: list[ArtistIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DiscIngestDTO:
    disc_number: int
    media_type: MediaType
    container_format: ContainerFormat
    catalog_number: str | None = None
    log_type: LogType | None = None
    log_score: int | None = None
    raw_log_text: str | None = None
    raw_cue_text: str | None = None
    accuraterip_summary: str | None = None
    tracks: list[TrackIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CoverIngestDTO:
    image_data: bytes
    cover_type: str = "Front"


@dataclass(frozen=True, slots=True)
class ArchiveLinkIngestDTO:
    provider_name: str
    download_url: str
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ArchiveIngestDTO:
    archive_name: str
    encryption_password: str = ""
    file_size_bytes: int | None = None
    hash_sha256: str | None = None
    links: list[ArchiveLinkIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ExternalLinkIngestDTO:
    site_name: str
    url: str


@dataclass(frozen=True, slots=True)
class IngestAlbumRequest:
    title_original: str
    original_folder_name: str
    album_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    title_translated: str | None = None
    release_year: int | None = None
    release_month: int | None = None
    release_day: int | None = None
    label: str | None = None
    publisher: str | None = None
    storage_drive: str | None = None
    relative_path: str | None = None
    event_id: uuid.UUID | None = None
    franchise_id: uuid.UUID | None = None
    album_artist_id: uuid.UUID | None = None
    album_artist: ArtistIngestDTO | None = None
    discs: list[DiscIngestDTO] = field(default_factory=list)
    covers: list[CoverIngestDTO] = field(default_factory=list)
    archives: list[ArchiveIngestDTO] = field(default_factory=list)
    external_links: list[ExternalLinkIngestDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class IngestAlbumResponse:
    album_id: uuid.UUID
    title_original: str
    total_discs: int
    total_tracks: int


class IngestAlbumUseCase:
    def __init__(
        self,
        album_repo: AlbumRepository,
        storage_service: MinioObjectStorageService | None = None,
    ) -> None:
        self._album_repo = album_repo
        self._storage_service = storage_service or MinioObjectStorageService()

    async def execute(self, request: IngestAlbumRequest) -> IngestAlbumResponse:
        album_id = request.album_id or uuid.uuid4()
        total_tracks_counter = 0

        domain_album_artist = None
        if request.album_artist:
            domain_album_artist = Artist(
                id=request.album_artist.id or uuid.uuid4(),
                name_original=request.album_artist.name_original,
                name_translated=request.album_artist.name_translated,
            )

        domain_discs: list[Disc] = []
        for disc_dto in request.discs:
            disc_id = uuid.uuid4()
            domain_tracks: list[Track] = []

            seen_track_numbers: set[int] = set()
            for t_idx, track_dto in enumerate(disc_dto.tracks, start=1):
                total_tracks_counter += 1
                track_id = uuid.uuid4()

                assigned_track_number = track_dto.track_number
                if assigned_track_number in seen_track_numbers or assigned_track_number <= 0:
                    assigned_track_number = t_idx
                seen_track_numbers.add(assigned_track_number)

                track_artists = [
                    Artist(
                        id=a.id or uuid.uuid4(),
                        name_original=a.name_original,
                        name_translated=a.name_translated,
                        role=a.role,
                    )
                    for a in track_dto.artists
                ]

                domain_tracks.append(
                    Track(
                        id=track_id,
                        disc_id=disc_id,
                        track_number=assigned_track_number,
                        title_original=track_dto.title_original,
                        title_translated=track_dto.title_translated,
                        duration_seconds=track_dto.duration_seconds,
                        audio_codec=track_dto.audio_codec,
                        video_codec=track_dto.video_codec,
                        bit_depth=track_dto.bit_depth,
                        sample_rate=track_dto.sample_rate,
                        bitrate_kbps=track_dto.bitrate_kbps,
                        bitrate_mode=track_dto.bitrate_mode,
                        is_instrumental=track_dto.is_instrumental,
                        artists=track_artists,
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
                    raw_log_text=disc_dto.raw_log_text,
                    raw_cue_text=disc_dto.raw_cue_text,
                    accuraterip_summary=disc_dto.accuraterip_summary,
                    tracks=domain_tracks,
                )
            )

        domain_covers: list[AlbumCover] = []
        for cover_dto in request.covers:
            cover_id = uuid.uuid4()
            object_key = f"covers/{album_id}/{cover_id}.jpg"
            storage_path, thumb_hash_str = await self._storage_service.upload_cover(
                object_key=object_key,
                data=cover_dto.image_data,
            )
            public_url = MinioObjectStorageService.get_public_url(storage_path)
            domain_covers.append(
                AlbumCover(
                    id=cover_id,
                    album_id=album_id,
                    storage_path=storage_path,
                    thumbhash=thumb_hash_str,
                    url=public_url,
                    cover_type=cover_dto.cover_type,
                )
            )

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
                    hash_sha256=archive_dto.hash_sha256,
                    links=domain_links,
                )
            )

        domain_external_links = [
            ExternalLink(
                id=uuid.uuid4(),
                album_id=album_id,
                site_name=link_dto.site_name,
                url=link_dto.url,
            )
            for link_dto in request.external_links
        ]

        album_aggregate = Album(
            id=album_id,
            title_original=request.title_original,
            title_translated=request.title_translated,
            release_year=request.release_year,
            release_month=request.release_month,
            release_day=request.release_day,
            label=request.label,
            publisher=request.publisher,
            event_id=request.event_id,
            franchise_id=request.franchise_id,
            album_artist_id=request.album_artist_id,
            album_artist=domain_album_artist,
            storage_drive=request.storage_drive,
            relative_path=request.relative_path,
            original_folder_name=request.original_folder_name,
            discs=domain_discs,
            covers=domain_covers,
            archives=domain_archives,
            external_links=domain_external_links,
        )

        await self._album_repo.save(album_aggregate, user_id=request.user_id)

        return IngestAlbumResponse(
            album_id=album_id,
            title_original=album_aggregate.title_original,
            total_discs=len(domain_discs),
            total_tracks=total_tracks_counter,
        )
