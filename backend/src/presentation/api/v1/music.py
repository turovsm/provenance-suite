import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.delete_album import (
    DeleteAlbumRequest,
    DeleteAlbumUseCase,
)
from src.application.use_cases.ingest_album import (
    ArchiveIngestDTO,
    ArchiveLinkIngestDTO,
    ArtistIngestDTO,
    CoverIngestDTO,
    DiscIngestDTO,
    ExternalLinkIngestDTO,
    IngestAlbumRequest,
    IngestAlbumUseCase,
    TrackIngestDTO,
)
from src.application.use_cases.list_albums import (
    GetAlbumDetailRequest,
    GetAlbumDetailUseCase,
    ListAlbumsRequest,
    ListAlbumsUseCase,
)
from src.domain.entities.user import User
from src.infrastructure.db.repositories.album import SqlAlchemyAlbumRepository
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.redis.client import get_redis
from src.infrastructure.storage.object_storage import MinioObjectStorageService
from src.presentation.api.dependencies import get_current_active_user, get_current_superuser
from src.presentation.schemas.music import (
    AlbumChangelogResponseSchema,
    AlbumDetailResponseSchema,
    AlbumIngestRequestSchema,
    AlbumIngestResponseSchema,
    AlbumSummaryResponseSchema,
    ArchiveLinkResponseSchema,
    ArchiveResponseSchema,
    ArtistResponseSchema,
    CoverResponseSchema,
    DiscResponseSchema,
    ExternalLinkResponseSchema,
    PaginatedAlbumsResponseSchema,
    TrackArtistResponseSchema,
    TrackResponseSchema,
)


router = APIRouter(prefix="/albums", tags=["Preservation Metadata Engine"])


@router.post(
    "",
    response_model=AlbumIngestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Ingest or update album aggregate root.",
)
async def ingest_album_endpoint(
    payload: AlbumIngestRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
    superuser: User = Depends(get_current_superuser),
) -> AlbumIngestResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session, redis=redis)
    storage_service = MinioObjectStorageService()
    use_case = IngestAlbumUseCase(album_repository, storage_service)

    domain_album_artist = None
    if payload.album_artist:
        domain_album_artist = ArtistIngestDTO(
            id=payload.album_artist.id,
            name_original=payload.album_artist.name_original,
            aliases=list(payload.album_artist.aliases),
        )

    use_case_discs = [
        DiscIngestDTO(
            disc_number=d.disc_number,
            media_type=d.media_type,
            container_format=d.container_format,
            catalog_number=d.catalog_number,
            log_type=d.log_type,
            log_score=d.log_score,
            raw_log_text=d.raw_log_text,
            raw_cue_text=d.raw_cue_text,
            accuraterip_summary=d.accuraterip_summary,
            tracks=[
                TrackIngestDTO(
                    track_number=t.track_number,
                    title_original=t.title_original,
                    aliases=list(t.aliases),
                    duration_seconds=t.duration_seconds,
                    audio_codec=t.audio_codec,
                    video_codec=t.video_codec,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                    bitrate_kbps=t.bitrate_kbps,
                    bitrate_mode=t.bitrate_mode,
                    is_instrumental=t.is_instrumental,
                    artists=[
                        ArtistIngestDTO(
                            id=a.id,
                            name_original=a.name_original,
                            aliases=list(a.aliases),
                            role=a.role,
                        )
                        for a in t.artists
                    ],
                )
                for t in d.tracks
            ],
        )
        for d in payload.discs
    ]

    use_case_covers = [
        CoverIngestDTO(
            image_data=c.image_data,
            cover_type=c.cover_type,
        )
        for c in payload.covers
    ]

    use_case_archives = [
        ArchiveIngestDTO(
            archive_name=a.archive_name,
            encryption_password=a.encryption_password,
            file_size_bytes=a.file_size_bytes,
            hash_sha256=a.hash_sha256,
            links=[ArchiveLinkIngestDTO(**lnk.model_dump()) for lnk in a.links],
        )
        for a in payload.archives
    ]

    use_case_external_links = [
        ExternalLinkIngestDTO(**el.model_dump()) for el in payload.external_links
    ]

    use_case_request = IngestAlbumRequest(
        album_id=payload.album_id,
        user_id=superuser.id,
        title_original=payload.title_original,
        original_folder_name=payload.original_folder_name,
        aliases=list(payload.aliases),
        storage_drive=payload.storage_drive,
        relative_path=payload.relative_path,
        release_year=payload.release_year,
        release_month=payload.release_month,
        release_day=payload.release_day,
        label=payload.label,
        publisher=payload.publisher,
        event_id=payload.event_id,
        franchise_id=payload.franchise_id,
        album_artist_id=payload.album_artist_id,
        album_artist=domain_album_artist,
        discs=use_case_discs,
        covers=use_case_covers,
        archives=use_case_archives,
        external_links=use_case_external_links,
    )

    response = await use_case.execute(use_case_request)
    await session.commit()

    return AlbumIngestResponseSchema(
        album_id=response.album_id,
        title_original=response.title_original,
        total_discs=response.total_discs,
        total_tracks=response.total_tracks,
    )


@router.get(
    "",
    response_model=PaginatedAlbumsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="[User/Admin] Search and paginate catalog albums.",
)
async def list_albums_endpoint(
    query: str | None = Query(default=None, description="Search term for title or folder name."),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
    _user=Depends(get_current_active_user),
) -> PaginatedAlbumsResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session, redis=redis)
    use_case = ListAlbumsUseCase(album_repository)

    request = ListAlbumsRequest(query=query, limit=limit, offset=offset)
    response = await use_case.execute(request)

    summaries = [
        AlbumSummaryResponseSchema(
            id=album.id,
            title_original=album.title_original,
            aliases=list(album.aliases),
            release_year=album.release_year,
            release_month=album.release_month,
            release_day=album.release_day,
            label=album.label,
            publisher=album.publisher,
            original_folder_name=album.original_folder_name,
            album_artist=ArtistResponseSchema.model_validate(album.album_artist)
            if album.album_artist
            else None,
            total_discs=len(album.discs),
            covers=[
                CoverResponseSchema(
                    id=c.id,
                    storage_path=c.storage_path,
                    thumbhash=c.thumbhash,
                    url=c.url or MinioObjectStorageService.get_public_url(c.storage_path),
                    cover_type=c.cover_type,
                    created_at=c.created_at,
                )
                for c in album.covers
            ],
        )
        for album in response.items
    ]

    return PaginatedAlbumsResponseSchema(
        items=summaries,
        total_count=response.total_count,
        limit=response.limit,
        offset=response.offset,
    )


@router.get(
    "/{album_id}",
    response_model=AlbumDetailResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="[User/Admin] Retrieve full aggregate detail for an album by ID.",
)
async def get_album_detail_endpoint(
    album_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
    _user=Depends(get_current_active_user),
) -> AlbumDetailResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session, redis=redis)
    use_case = GetAlbumDetailUseCase(album_repository)

    album = await use_case.execute(GetAlbumDetailRequest(album_id=album_id))

    discs_dto = [
        DiscResponseSchema(
            id=d.id,
            disc_number=d.disc_number,
            catalog_number=d.catalog_number,
            media_type=d.media_type,
            container_format=d.container_format,
            log_type=d.log_type,
            log_score=d.log_score,
            raw_log_text=d.raw_log_text,
            raw_cue_text=d.raw_cue_text,
            accuraterip_summary=d.accuraterip_summary,
            tracks=[
                TrackResponseSchema(
                    id=t.id,
                    track_number=t.track_number,
                    title_original=t.title_original,
                    aliases=list(t.aliases),
                    duration_seconds=t.duration_seconds,
                    audio_codec=t.audio_codec,
                    video_codec=t.video_codec,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                    bitrate_kbps=t.bitrate_kbps,
                    bitrate_mode=t.bitrate_mode,
                    is_instrumental=t.is_instrumental,
                    artists=[TrackArtistResponseSchema.model_validate(ta) for ta in t.artists],
                )
                for t in d.tracks
            ],
        )
        for d in album.discs
    ]

    album_artist_dto = (
        ArtistResponseSchema.model_validate(album.album_artist) if album.album_artist else None
    )

    covers_dto = [
        CoverResponseSchema(
            id=c.id,
            storage_path=c.storage_path,
            thumbhash=c.thumbhash,
            url=c.url or MinioObjectStorageService.get_public_url(c.storage_path),
            cover_type=c.cover_type,
            created_at=c.created_at,
        )
        for c in album.covers
    ]

    archives_dto = [
        ArchiveResponseSchema(
            id=a.id,
            archive_name=a.archive_name,
            encryption_password=a.encryption_password,
            file_size_bytes=a.file_size_bytes,
            hash_sha256=a.hash_sha256,
            links=[
                ArchiveLinkResponseSchema(
                    id=lnk.id,
                    provider_name=lnk.provider_name,
                    download_url=lnk.download_url,
                    is_active=lnk.is_active,
                )
                for lnk in a.links
            ],
        )
        for a in album.archives
    ]

    external_links_dto = [
        ExternalLinkResponseSchema(
            id=el.id,
            site_name=el.site_name,
            url=el.url,
        )
        for el in album.external_links
    ]

    changelogs_dto = [
        AlbumChangelogResponseSchema(
            id=cl.id,
            user_id=cl.user_id,
            action=cl.action,
            changes=cl.changes,
            created_at=cl.created_at,
        )
        for cl in album.changelogs
    ]

    return AlbumDetailResponseSchema(
        id=album.id,
        title_original=album.title_original,
        aliases=list(album.aliases),
        release_year=album.release_year,
        release_month=album.release_month,
        release_day=album.release_day,
        label=album.label,
        publisher=album.publisher,
        storage_drive=album.storage_drive,
        relative_path=album.relative_path,
        event_id=album.event_id,
        franchise_id=album.franchise_id,
        original_folder_name=album.original_folder_name,
        album_artist=album_artist_dto,
        discs=discs_dto,
        covers=covers_dto,
        archives=archives_dto,
        external_links=external_links_dto,
        changelogs=changelogs_dto,
    )


@router.delete(
    "/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Delete album aggregate root by ID.",
)
async def delete_album_endpoint(
    album_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    redis: aioredis.Redis = Depends(get_redis),
    _superuser: User = Depends(get_current_superuser),
) -> None:
    album_repository = SqlAlchemyAlbumRepository(session, redis=redis)
    use_case = DeleteAlbumUseCase(album_repository)

    await use_case.execute(DeleteAlbumRequest(album_id=album_id))
    await session.commit()
