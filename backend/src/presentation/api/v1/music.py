from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from src.infrastructure.db.repositories.album import SqlAlchemyAlbumRepository
from src.infrastructure.db.session import get_async_database_session
from src.presentation.api.dependencies import get_current_active_user
from src.presentation.schemas.music import AlbumIngestRequestSchema, AlbumIngestResponseSchema


router = APIRouter(prefix="/albums", tags=["Preservation Metadata Ingestion Plane"])


@router.post(
    "",
    response_model=AlbumIngestResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a fully formed high-fidelity multi-disc metadata aggregate graph node.",
)
async def ingest_album_endpoint(
    payload: AlbumIngestRequestSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _current_user=Depends(get_current_active_user),
) -> AlbumIngestResponseSchema:
    # 1. Instantiate persistence layer components
    album_repository = SqlAlchemyAlbumRepository(session)
    use_case = IngestAlbumUseCase(album_repository)

    # 2. Map structural inbound schema payload elements to UseCase DTO structures
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

    # 3. Construct unified use case request message package
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
        # 4. Process deep relation write routines and execute session commits
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
