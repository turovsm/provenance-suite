import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.delete_album import (
    AlbumNotFoundError,
    DeleteAlbumRequest,
    DeleteAlbumUseCase,
)
from src.application.use_cases.ingest_album import (
    ArchiveIngestDTO,
    ArchiveLinkIngestDTO,
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
from src.domain.value_objects.music_types import LibraryCategory
from src.infrastructure.db.repositories.album import SqlAlchemyAlbumRepository
from src.infrastructure.db.session import get_async_database_session
from src.presentation.api.dependencies import get_current_active_user, get_current_superuser
from src.presentation.schemas.music import (
    AlbumDetailResponseSchema,
    AlbumIngestRequestSchema,
    AlbumIngestResponseSchema,
    AlbumSummaryResponseSchema,
    ArchiveLinkResponseSchema,
    ArchiveResponseSchema,
    DiscResponseSchema,
    ExternalLinkResponseSchema,
    PaginatedAlbumsResponseSchema,
    TrackResponseSchema,
)


router = APIRouter(prefix="/albums", tags=["Preservation Metadata Engine"])


# --- Admin-Only Mutative Endpoints (RBAC: get_current_superuser) ---


@router.post(
    "",
    response_model=AlbumIngestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Ingest a fully formed high-fidelity multi-disc metadata aggregate graph node.",
)
async def ingest_album_endpoint(
    payload: AlbumIngestRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _superuser=Depends(get_current_superuser),
) -> AlbumIngestResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session)
    use_case = IngestAlbumUseCase(album_repository)

    use_case_discs = [
        DiscIngestDTO(
            disc_number=d.disc_number,
            media_type=d.media_type,
            container_format=d.container_format,
            catalog_number=d.catalog_number,
            log_type=d.log_type,
            log_score=d.log_score,
            tracks=[TrackIngestDTO(**t.model_dump()) for t in d.tracks],
        )
        for d in payload.discs
    ]

    use_case_archives = [
        ArchiveIngestDTO(
            archive_name=a.archive_name,
            encryption_password=a.encryption_password,
            file_size_bytes=a.file_size_bytes,
            links=[ArchiveLinkIngestDTO(**lnk.model_dump()) for lnk in a.links],
        )
        for a in payload.archives
    ]

    use_case_external_links = [
        ExternalLinkIngestDTO(**el.model_dump()) for el in payload.external_links
    ]

    use_case_cover = None
    if payload.cover:
        use_case_cover = CoverIngestDTO(
            image_data=payload.cover.image_data,
            mime_type=payload.cover.mime_type,
            width=payload.cover.width,
            height=payload.cover.height,
        )

    use_case_request = IngestAlbumRequest(
        title_original=payload.title_original,
        library_category=payload.library_category,
        original_folder_name=payload.original_folder_name,
        title_translated=payload.title_translated,
        release_date=payload.release_date,
        event_id=payload.event_id,
        franchise_id=payload.franchise_id,
        discs=use_case_discs,
        archives=use_case_archives,
        external_links=use_case_external_links,
        cover=use_case_cover,
    )

    try:
        response = await use_case.execute(use_case_request)
        await session.commit()

        return AlbumIngestResponseSchema(
            album_id=response.album_id,
            title_original=response.title_original,
            total_discs=response.total_discs,
            total_tracks=response.total_tracks,
        )
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected exception encountered processing catalog ingestion frame.",
        ) from exc


@router.delete(
    "/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Remove an album aggregate root and all cascading child records.",
)
async def delete_album_endpoint(
    album_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _superuser=Depends(get_current_superuser),
) -> None:
    album_repository = SqlAlchemyAlbumRepository(session)
    use_case = DeleteAlbumUseCase(album_repository)

    try:
        await use_case.execute(DeleteAlbumRequest(album_id=album_id))
        await session.commit()
    except AlbumNotFoundError as exc:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error occurred during album deletion.",
        ) from exc


# --- User & Admin Read Endpoints (RBAC: get_current_active_user) ---


@router.get(
    "",
    response_model=PaginatedAlbumsResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="[User/Admin] Search and paginate through the album collection catalogue.",
)
async def list_albums_endpoint(
    category: LibraryCategory | None = Query(
        default=None, description="Optional library partition category."
    ),
    query: str | None = Query(default=None, description="Search term for title or folder name."),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
) -> PaginatedAlbumsResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session)
    use_case = ListAlbumsUseCase(album_repository)

    request = ListAlbumsRequest(category=category, query=query, limit=limit, offset=offset)
    response = await use_case.execute(request)

    summaries = [
        AlbumSummaryResponseSchema(
            id=album.id,
            title_original=album.title_original,
            title_translated=album.title_translated,
            release_date=album.release_date,
            library_category=album.library_category,
            original_folder_name=album.original_folder_name,
            total_discs=len(album.discs),
            has_cover=album.cover is not None,
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
    summary="[User/Admin] Retrieve full aggregate detail for a specific album by ID.",
)
async def get_album_detail_endpoint(
    album_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
) -> AlbumDetailResponseSchema:
    album_repository = SqlAlchemyAlbumRepository(session)
    use_case = GetAlbumDetailUseCase(album_repository)

    album = await use_case.execute(GetAlbumDetailRequest(album_id=album_id))
    if album is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Album record with ID '{album_id}' was not found.",
        )

    discs_dto = [
        DiscResponseSchema(
            id=d.id,
            disc_number=d.disc_number,
            catalog_number=d.catalog_number,
            media_type=d.media_type,
            container_format=d.container_format,
            tracks=[
                TrackResponseSchema(
                    id=t.id,
                    track_number=t.track_number,
                    title_original=t.title_original,
                    title_translated=t.title_translated,
                    duration_seconds=t.duration_seconds,
                    audio_codec=t.audio_codec,
                    bit_depth=t.bit_depth,
                    sample_rate=t.sample_rate,
                )
                for t in d.tracks
            ],
        )
        for d in album.discs
    ]

    archives_dto = [
        ArchiveResponseSchema(
            id=a.id,
            archive_name=a.archive_name,
            encryption_password=a.encryption_password,
            file_size_bytes=a.file_size_bytes,
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
            remote_item_id=el.remote_item_id,
        )
        for el in album.external_links
    ]

    return AlbumDetailResponseSchema(
        id=album.id,
        title_original=album.title_original,
        title_translated=album.title_translated,
        release_date=album.release_date,
        library_category=album.library_category,
        original_folder_name=album.original_folder_name,
        discs=discs_dto,
        archives=archives_dto,
        external_links=external_links_dto,
        has_cover=album.cover is not None,
    )
