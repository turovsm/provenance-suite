import uuid
from datetime import date
from typing import Any, TypeVar

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import Text, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.value_objects.aliases import normalize_aliases
from src.infrastructure.db.models.base import BaseInfrastructureModel
from src.infrastructure.db.models.music import (
    AlbumModel,
    ArtistModel,
    DiscModel,
    EventModel,
    FranchiseModel,
    LabelModel,
    PublisherModel,
    TrackArtistModel,
    TrackModel,
)
from src.infrastructure.db.session import get_async_database_session
from src.infrastructure.storage.object_storage import MinioObjectStorageService
from src.presentation.api.dependencies import get_optional_current_user, require_admin
from src.presentation.api.helpers import (
    fetch_albums_by_entity_fk,
    find_existing_entity_by_name,
    get_entity_or_404,
    search_named_entities,
)
from src.presentation.schemas.entities import (
    ArtistCreateSchema,
    ArtistResponseSchema,
    ArtistUpdateSchema,
    EntitySummarySchema,
    EventCreateSchema,
    EventResponseSchema,
    EventUpdateSchema,
    FranchiseCreateSchema,
    FranchiseResponseSchema,
    FranchiseUpdateSchema,
    LabelCreateSchema,
    LabelResponseSchema,
    LabelUpdateSchema,
    PaginatedEntitiesResponseSchema,
    PaginatedEventsResponseSchema,
    PublisherCreateSchema,
    PublisherResponseSchema,
    PublisherUpdateSchema,
)
from src.presentation.schemas.music import (
    AlbumSummaryResponseSchema,
    CoverResponseSchema,
)


router = APIRouter(prefix="/entities", tags=["Master Entity Registry"])

ModelT = TypeVar("ModelT", bound=BaseInfrastructureModel)


def get_image_url(image_path: str | None) -> str | None:
    if not image_path:
        return None
    return MinioObjectStorageService.get_public_url(image_path)


def map_artist_response(model: ArtistModel) -> ArtistResponseSchema:
    return ArtistResponseSchema(
        id=model.id,
        name_original=model.name_original,
        aliases=list(model.aliases or []),
        image_url=get_image_url(model.image_path),
        description=model.description,
        created_at=model.created_at,
    )


def map_franchise_response(model: FranchiseModel) -> FranchiseResponseSchema:
    return FranchiseResponseSchema(
        id=model.id,
        name_original=model.name_original,
        aliases=list(model.aliases or []),
        franchise_type=model.franchise_type,
        image_url=get_image_url(model.image_path),
        description=model.description,
        created_at=model.created_at,
    )


def map_label_response(model: LabelModel) -> LabelResponseSchema:
    return LabelResponseSchema(
        id=model.id,
        name_original=model.name_original,
        aliases=list(model.aliases or []),
        image_url=get_image_url(model.image_path),
        description=model.description,
        created_at=model.created_at,
    )


def map_publisher_response(model: PublisherModel) -> PublisherResponseSchema:
    return PublisherResponseSchema(
        id=model.id,
        name_original=model.name_original,
        aliases=list(model.aliases or []),
        image_url=get_image_url(model.image_path),
        description=model.description,
        created_at=model.created_at,
    )


def map_album_summary(album: AlbumModel) -> AlbumSummaryResponseSchema:
    album_artist_dto = (
        ArtistResponseSchema(
            id=album.album_artist.id,
            name_original=album.album_artist.name_original,
            aliases=list(album.album_artist.aliases or []),
            image_url=get_image_url(album.album_artist.image_path),
            description=album.album_artist.description,
            created_at=album.album_artist.created_at,
        )
        if album.album_artist
        else None
    )

    label_dto = (
        LabelResponseSchema(
            id=album.label.id,
            name_original=album.label.name_original,
            aliases=list(album.label.aliases or []),
            image_url=get_image_url(album.label.image_path),
            description=album.label.description,
            created_at=album.label.created_at,
        )
        if album.label
        else None
    )

    publisher_dto = (
        PublisherResponseSchema(
            id=album.publisher.id,
            name_original=album.publisher.name_original,
            aliases=list(album.publisher.aliases or []),
            image_url=get_image_url(album.publisher.image_path),
            description=album.publisher.description,
            created_at=album.publisher.created_at,
        )
        if album.publisher
        else None
    )

    covers = [
        CoverResponseSchema(
            id=c.id,
            storage_path=c.storage_path,
            thumbhash=c.thumbhash,
            url=MinioObjectStorageService.get_public_url(c.storage_path),
            cover_type=c.cover_type,
            created_at=c.created_at,
        )
        for c in album.covers
    ]

    return AlbumSummaryResponseSchema(
        id=album.id,
        title_original=album.title_original,
        aliases=list(album.aliases or []),
        release_year=album.release_year,
        release_month=album.release_month,
        release_day=album.release_day,
        label=label_dto,
        publisher=publisher_dto,
        original_folder_name=album.original_folder_name,
        album_artist=album_artist_dto,
        total_discs=len(album.discs),
        covers=covers,
    )


async def _process_image_upload(
    storage_service: MinioObjectStorageService,
    entity_type: str,
    entity_id: uuid.UUID,
    image_data_bytes: bytes | None,
) -> str | None:
    if not image_data_bytes:
        return None
    return await storage_service.upload_entity_avatar(entity_type, entity_id, image_data_bytes)


def _merge_aliases(existing: list[str] | None, incoming: list[str]) -> list[str]:
    merged = list(existing or [])
    seen = {a.casefold() for a in merged}
    for alias in normalize_aliases(incoming):
        if alias.casefold() not in seen:
            merged.append(alias)
            seen.add(alias.casefold())
    return merged


@router.get("", response_model=PaginatedEntitiesResponseSchema)
async def list_unified_entities(
    type: str = Query(
        default="all",
        description="Entity type filter: all, artist, franchise, label, publisher",
    ),
    query: str = Query(default=""),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    q = query.strip()
    items: list[EntitySummarySchema] = []

    entity_targets = []
    if type in ("all", "artist"):
        entity_targets.append(("artist", ArtistModel))
    if type in ("all", "franchise"):
        entity_targets.append(("franchise", FranchiseModel))
    if type in ("all", "label"):
        entity_targets.append(("label", LabelModel))
    if type in ("all", "publisher"):
        entity_targets.append(("publisher", PublisherModel))

    total_count = 0
    for e_type, model_cls in entity_targets:
        stmt = select(model_cls)
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    model_cls.name_original.ilike(pattern),
                    cast(model_cls.aliases, Text).ilike(pattern),
                )
            )

        res_count = await session.execute(select(func.count()).select_from(stmt.subquery()))
        total_count += res_count.scalar_one()

        res_rows = await session.execute(stmt.order_by(model_cls.name_original))
        rows = res_rows.scalars().all()

        for row in rows:
            items.append(
                EntitySummarySchema(
                    id=row.id,
                    name_original=row.name_original,
                    aliases=list(row.aliases or []),
                    entity_type=e_type,
                    image_url=get_image_url(row.image_path),
                    description=row.description,
                    franchise_type=getattr(row, "franchise_type", None),
                    created_at=row.created_at,
                )
            )

    items.sort(key=lambda x: x.name_original.lower())
    paginated_items = items[offset : offset + limit]

    return PaginatedEntitiesResponseSchema(
        items=paginated_items,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/artists", response_model=list[ArtistResponseSchema])
async def search_artists(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    artists = await search_named_entities(session, ArtistModel, query=query, limit=limit)
    return [map_artist_response(a) for a in artists]


@router.get("/artists/{artist_id}", response_model=ArtistResponseSchema)
async def get_artist_detail(
    artist_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    artist = await get_entity_or_404(session, ArtistModel, artist_id, "Artist")
    return map_artist_response(artist)


@router.get("/artists/{artist_id}/discography")
async def get_artist_discography(
    artist_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    main_albums_models = await fetch_albums_by_entity_fk(
        session, AlbumModel.album_artist_id, artist_id
    )
    main_albums = [map_album_summary(a) for a in main_albums_models]

    contrib_stmt = (
        select(AlbumModel)
        .join(DiscModel, DiscModel.album_id == AlbumModel.id)
        .join(TrackModel, TrackModel.disc_id == DiscModel.id)
        .join(TrackArtistModel, TrackArtistModel.track_id == TrackModel.id)
        .where(
            TrackArtistModel.artist_id == artist_id,
            or_(AlbumModel.album_artist_id.is_(None), AlbumModel.album_artist_id != artist_id),
        )
        .distinct()
        .options(
            selectinload(AlbumModel.covers),
            selectinload(AlbumModel.album_artist),
            selectinload(AlbumModel.label),
            selectinload(AlbumModel.publisher),
            selectinload(AlbumModel.discs),
        )
        .order_by(AlbumModel.release_date_sort.desc().nulls_last())
    )
    contrib_res = await session.execute(contrib_stmt)
    contribution_albums = [map_album_summary(a) for a in contrib_res.unique().scalars().all()]

    return {
        "artist_id": artist_id,
        "main_albums": main_albums,
        "contribution_albums": contribution_albums,
    }


@router.post("/artists", response_model=ArtistResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_artist(
    payload: ArtistCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    clean_name = payload.name_original.strip()
    existing = await find_existing_entity_by_name(session, ArtistModel, clean_name)

    artist_id = existing.id if existing else uuid.uuid4()
    storage_service = MinioObjectStorageService()
    image_path = await _process_image_upload(
        storage_service, "artist", artist_id, payload.image_data
    )

    if existing:
        existing.aliases = _merge_aliases(existing.aliases, payload.aliases)
        if payload.description is not None:
            existing.description = payload.description
        if image_path:
            existing.image_path = image_path
        await session.commit()
        await session.refresh(existing)
        return map_artist_response(existing)

    new_artist = ArtistModel(
        id=artist_id,
        name_original=clean_name,
        aliases=normalize_aliases(payload.aliases),
        description=payload.description,
        image_path=image_path,
    )
    session.add(new_artist)
    await session.commit()
    await session.refresh(new_artist)
    return map_artist_response(new_artist)


@router.put("/artists/{artist_id}", response_model=ArtistResponseSchema)
async def update_artist(
    artist_id: uuid.UUID,
    payload: ArtistUpdateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    artist = await get_entity_or_404(session, ArtistModel, artist_id, "Artist")

    if payload.name_original is not None:
        artist.name_original = payload.name_original.strip()
    if payload.aliases is not None:
        artist.aliases = normalize_aliases(payload.aliases)
    if payload.description is not None:
        artist.description = payload.description

    if payload.image_data is not None:
        storage_service = MinioObjectStorageService()
        if artist.image_path:
            await storage_service.delete_cover(artist.image_path)
        if len(payload.image_data) > 0:
            artist.image_path = await storage_service.upload_entity_avatar(
                "artist", artist_id, payload.image_data
            )
        else:
            artist.image_path = None

    await session.commit()
    await session.refresh(artist)
    return map_artist_response(artist)


@router.delete("/artists/{artist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artist(
    artist_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    artist = await get_entity_or_404(session, ArtistModel, artist_id, "Artist")
    await session.delete(artist)
    await session.commit()


@router.get("/franchises", response_model=list[FranchiseResponseSchema])
async def search_franchises(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    franchises = await search_named_entities(session, FranchiseModel, query=query, limit=limit)
    return [map_franchise_response(f) for f in franchises]


@router.get("/franchises/{franchise_id}", response_model=FranchiseResponseSchema)
async def get_franchise_detail(
    franchise_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    franchise = await get_entity_or_404(session, FranchiseModel, franchise_id, "Franchise")
    return map_franchise_response(franchise)


@router.get("/franchises/{franchise_id}/albums", response_model=list[AlbumSummaryResponseSchema])
async def get_franchise_albums(
    franchise_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    albums = await fetch_albums_by_entity_fk(session, AlbumModel.franchise_id, franchise_id)
    return [map_album_summary(a) for a in albums]


@router.post(
    "/franchises",
    response_model=FranchiseResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_franchise(
    payload: FranchiseCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    clean_name = payload.name_original.strip()
    existing = await find_existing_entity_by_name(session, FranchiseModel, clean_name)

    f_id = existing.id if existing else uuid.uuid4()
    storage_service = MinioObjectStorageService()
    image_path = await _process_image_upload(storage_service, "franchise", f_id, payload.image_data)

    if existing:
        existing.aliases = _merge_aliases(existing.aliases, payload.aliases)
        existing.franchise_type = payload.franchise_type
        if payload.description is not None:
            existing.description = payload.description
        if image_path:
            existing.image_path = image_path
        await session.commit()
        await session.refresh(existing)
        return map_franchise_response(existing)

    new_f = FranchiseModel(
        id=f_id,
        name_original=clean_name,
        aliases=normalize_aliases(payload.aliases),
        franchise_type=payload.franchise_type,
        description=payload.description,
        image_path=image_path,
    )
    session.add(new_f)
    await session.commit()
    await session.refresh(new_f)
    return map_franchise_response(new_f)


@router.put("/franchises/{franchise_id}", response_model=FranchiseResponseSchema)
async def update_franchise(
    franchise_id: uuid.UUID,
    payload: FranchiseUpdateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    franchise = await get_entity_or_404(session, FranchiseModel, franchise_id, "Franchise")

    if payload.name_original is not None:
        franchise.name_original = payload.name_original.strip()
    if payload.aliases is not None:
        franchise.aliases = normalize_aliases(payload.aliases)
    if payload.franchise_type is not None:
        franchise.franchise_type = payload.franchise_type
    if payload.description is not None:
        franchise.description = payload.description

    if payload.image_data is not None:
        storage_service = MinioObjectStorageService()
        if franchise.image_path:
            await storage_service.delete_cover(franchise.image_path)
        if len(payload.image_data) > 0:
            franchise.image_path = await storage_service.upload_entity_avatar(
                "franchise", franchise_id, payload.image_data
            )
        else:
            franchise.image_path = None

    await session.commit()
    await session.refresh(franchise)
    return map_franchise_response(franchise)


@router.delete("/franchises/{franchise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_franchise(
    franchise_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    franchise = await get_entity_or_404(session, FranchiseModel, franchise_id, "Franchise")
    await session.delete(franchise)
    await session.commit()


@router.get("/labels", response_model=list[LabelResponseSchema])
async def search_labels(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    labels = await search_named_entities(session, LabelModel, query=query, limit=limit)
    return [map_label_response(lbl) for lbl in labels]


@router.get("/labels/{label_id}", response_model=LabelResponseSchema)
async def get_label_detail(
    label_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    label = await get_entity_or_404(session, LabelModel, label_id, "Label")
    return map_label_response(label)


@router.get("/labels/{label_id}/albums", response_model=list[AlbumSummaryResponseSchema])
async def get_label_albums(
    label_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    albums = await fetch_albums_by_entity_fk(session, AlbumModel.label_id, label_id)
    return [map_album_summary(a) for a in albums]


@router.post("/labels", response_model=LabelResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_label(
    payload: LabelCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    clean_name = payload.name_original.strip()
    existing = await find_existing_entity_by_name(session, LabelModel, clean_name)

    l_id = existing.id if existing else uuid.uuid4()
    storage_service = MinioObjectStorageService()
    image_path = await _process_image_upload(storage_service, "label", l_id, payload.image_data)

    if existing:
        existing.aliases = _merge_aliases(existing.aliases, payload.aliases)
        if payload.description is not None:
            existing.description = payload.description
        if image_path:
            existing.image_path = image_path
        await session.commit()
        await session.refresh(existing)
        return map_label_response(existing)

    new_l = LabelModel(
        id=l_id,
        name_original=clean_name,
        aliases=normalize_aliases(payload.aliases),
        description=payload.description,
        image_path=image_path,
    )
    session.add(new_l)
    await session.commit()
    await session.refresh(new_l)
    return map_label_response(new_l)


@router.put("/labels/{label_id}", response_model=LabelResponseSchema)
async def update_label(
    label_id: uuid.UUID,
    payload: LabelUpdateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    label = await get_entity_or_404(session, LabelModel, label_id, "Label")

    if payload.name_original is not None:
        label.name_original = payload.name_original.strip()
    if payload.aliases is not None:
        label.aliases = normalize_aliases(payload.aliases)
    if payload.description is not None:
        label.description = payload.description

    if payload.image_data is not None:
        storage_service = MinioObjectStorageService()
        if label.image_path:
            await storage_service.delete_cover(label.image_path)
        if len(payload.image_data) > 0:
            label.image_path = await storage_service.upload_entity_avatar(
                "label", label_id, payload.image_data
            )
        else:
            label.image_path = None

    await session.commit()
    await session.refresh(label)
    return map_label_response(label)


@router.delete("/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    label = await get_entity_or_404(session, LabelModel, label_id, "Label")
    await session.delete(label)
    await session.commit()


@router.get("/publishers", response_model=list[PublisherResponseSchema])
async def search_publishers(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    publishers = await search_named_entities(session, PublisherModel, query=query, limit=limit)
    return [map_publisher_response(p) for p in publishers]


@router.get("/publishers/{publisher_id}", response_model=PublisherResponseSchema)
async def get_publisher_detail(
    publisher_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    publisher = await get_entity_or_404(session, PublisherModel, publisher_id, "Publisher")
    return map_publisher_response(publisher)


@router.get("/publishers/{publisher_id}/albums", response_model=list[AlbumSummaryResponseSchema])
async def get_publisher_albums(
    publisher_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    albums = await fetch_albums_by_entity_fk(session, AlbumModel.publisher_id, publisher_id)
    return [map_album_summary(a) for a in albums]


@router.post(
    "/publishers",
    response_model=PublisherResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_publisher(
    payload: PublisherCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    clean_name = payload.name_original.strip()
    existing = await find_existing_entity_by_name(session, PublisherModel, clean_name)

    p_id = existing.id if existing else uuid.uuid4()
    storage_service = MinioObjectStorageService()
    image_path = await _process_image_upload(storage_service, "publisher", p_id, payload.image_data)

    if existing:
        existing.aliases = _merge_aliases(existing.aliases, payload.aliases)
        if payload.description is not None:
            existing.description = payload.description
        if image_path:
            existing.image_path = image_path
        await session.commit()
        await session.refresh(existing)
        return map_publisher_response(existing)

    new_p = PublisherModel(
        id=p_id,
        name_original=clean_name,
        aliases=normalize_aliases(payload.aliases),
        description=payload.description,
        image_path=image_path,
    )
    session.add(new_p)
    await session.commit()
    await session.refresh(new_p)
    return map_publisher_response(new_p)


@router.put("/publishers/{publisher_id}", response_model=PublisherResponseSchema)
async def update_publisher(
    publisher_id: uuid.UUID,
    payload: PublisherUpdateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    publisher = await get_entity_or_404(session, PublisherModel, publisher_id, "Publisher")

    if payload.name_original is not None:
        publisher.name_original = payload.name_original.strip()
    if payload.aliases is not None:
        publisher.aliases = normalize_aliases(payload.aliases)
    if payload.description is not None:
        publisher.description = payload.description

    if payload.image_data is not None:
        storage_service = MinioObjectStorageService()
        if publisher.image_path:
            await storage_service.delete_cover(publisher.image_path)
        if len(payload.image_data) > 0:
            publisher.image_path = await storage_service.upload_entity_avatar(
                "publisher", publisher_id, payload.image_data
            )
        else:
            publisher.image_path = None

    await session.commit()
    await session.refresh(publisher)
    return map_publisher_response(publisher)


@router.delete("/publishers/{publisher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_publisher(
    publisher_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    publisher = await get_entity_or_404(session, PublisherModel, publisher_id, "Publisher")
    await session.delete(publisher)
    await session.commit()


def normalize_date_string(d: str | None) -> str | None:
    if not d or not d.strip():
        return None
    return d.strip().replace("/", "-").replace(".", "-")


def _parse_date_part(part: str, default_if_xx: int) -> int:
    clean = part.lower().strip()
    return default_if_xx if clean == "xx" else int(clean)


def _resolve_last_day_of_month(year: int, month: int) -> int:
    if month in (4, 6, 9, 11):
        return 30
    if month == 2:
        is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        return 29 if is_leap else 28
    return 31


def _construct_date_with_fallback(y: int, m: int, d_num: int, is_end_bound: bool) -> date | None:
    try:
        return date(y, m, d_num)
    except ValueError:
        if is_end_bound:
            last_day = _resolve_last_day_of_month(y, m)
            return date(y, m, last_day)
        return date(y, m, 1)


def compute_event_sort_date(d: str | None, is_end_bound: bool = False) -> date | None:
    norm = normalize_date_string(d)
    if not norm:
        return None
    parts = norm.split("-")
    if len(parts) != 3:
        return None
    try:
        y = int(parts[0])
        m = _parse_date_part(parts[1], 12 if is_end_bound else 1)
        d_num = _parse_date_part(parts[2], 31 if is_end_bound else 1)
        return _construct_date_with_fallback(y, m, d_num, is_end_bound)
    except ValueError:
        return None


def _apply_event_filters(
    stmt: Any,
    query: str | None,
    status_filter: list[str] | None,
    date_from: str | None,
    date_to: str | None,
) -> Any:
    if query and query.strip():
        q = f"%{query.strip()}%"
        stmt = stmt.where(or_(EventModel.short_name.ilike(q), EventModel.full_name.ilike(q)))

    if status_filter:
        flat_statuses = [
            item.strip().upper() for s in status_filter for item in s.split(",") if item.strip()
        ]
        if flat_statuses:
            stmt = stmt.where(func.upper(EventModel.status).in_(flat_statuses))

    if date_from:
        parsed_from = compute_event_sort_date(date_from, is_end_bound=False)
        if parsed_from:
            stmt = stmt.where(EventModel.start_date_sort >= parsed_from)

    if date_to:
        parsed_to = compute_event_sort_date(date_to, is_end_bound=True)
        if parsed_to:
            stmt = stmt.where(EventModel.start_date_sort <= parsed_to)

    return stmt


def _resolve_event_sort_order(sort_by: str, sort_order: str) -> Any:
    if sort_by == "short_name":
        sort_col = EventModel.short_name
    elif sort_by == "status":
        sort_col = EventModel.status
    else:
        sort_col = EventModel.start_date_sort

    if sort_order.lower() == "asc":
        return sort_col.asc().nulls_last()
    return sort_col.desc().nulls_last()


@router.get("/events", response_model=PaginatedEventsResponseSchema)
async def search_events(
    query: str | None = Query(default=None),
    status_filter: list[str] | None = Query(default=None, alias="status"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    sort_by: str = Query(default="start_date"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    stmt = _apply_event_filters(select(EventModel), query, status_filter, date_from, date_to)

    subq = stmt.subquery()
    count_stmt = select(func.count()).select_from(subq)
    total_count = (await session.execute(count_stmt)).scalar_one()

    order_clause = _resolve_event_sort_order(sort_by, sort_order)
    fetch_stmt = (
        stmt.order_by(order_clause, EventModel.short_name.asc()).offset(offset).limit(limit)
    )
    result = await session.execute(fetch_stmt)
    events = result.scalars().all()

    return PaginatedEventsResponseSchema(
        items=events,
        total_count=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/events/{event_id}", response_model=EventResponseSchema)
async def get_event_detail(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_optional_current_user),
):
    return await get_entity_or_404(session, EventModel, event_id, "Event")


@router.post("/events", response_model=EventResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    existing = await find_existing_entity_by_name(
        session, EventModel, payload.short_name, name_attr="short_name"
    )
    if existing:
        return existing

    start_norm = normalize_date_string(payload.start_date)
    end_norm = normalize_date_string(payload.end_date)
    orig_start_norm = normalize_date_string(payload.original_start_date)
    orig_end_norm = normalize_date_string(payload.original_end_date)
    start_sort = compute_event_sort_date(start_norm, is_end_bound=False)

    new_event = EventModel(
        id=uuid.uuid4(),
        short_name=payload.short_name.strip(),
        full_name=payload.full_name.strip() if payload.full_name else None,
        start_date=start_norm,
        end_date=end_norm,
        original_start_date=orig_start_norm,
        original_end_date=orig_end_norm,
        start_date_sort=start_sort,
        date_history=[d.model_dump(mode="json") for d in payload.date_history],
        additional_dates=[d.model_dump(mode="json") for d in payload.additional_dates],
        status=payload.status,
    )
    session.add(new_event)
    await session.commit()
    await session.refresh(new_event)
    return new_event


@router.put("/events/{event_id}", response_model=EventResponseSchema)
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    event = await get_entity_or_404(session, EventModel, event_id, "Event")

    if payload.short_name is not None:
        event.short_name = payload.short_name.strip()
    if payload.full_name is not None:
        event.full_name = payload.full_name.strip() if payload.full_name else None
    if payload.start_date is not None:
        event.start_date = normalize_date_string(payload.start_date)
        event.start_date_sort = compute_event_sort_date(event.start_date, is_end_bound=False)
    if payload.end_date is not None:
        event.end_date = normalize_date_string(payload.end_date)
    if payload.original_start_date is not None:
        event.original_start_date = normalize_date_string(payload.original_start_date)
    if payload.original_end_date is not None:
        event.original_end_date = normalize_date_string(payload.original_end_date)
    if payload.date_history is not None:
        event.date_history = [d.model_dump(mode="json") for d in payload.date_history]
    if payload.additional_dates is not None:
        event.additional_dates = [d.model_dump(mode="json") for d in payload.additional_dates]
    if payload.status is not None:
        event.status = payload.status

    await session.commit()
    await session.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_database_session),
    _admin=Depends(require_admin),
):
    event = await get_entity_or_404(session, EventModel, event_id, "Event")
    await session.delete(event)
    await session.commit()
