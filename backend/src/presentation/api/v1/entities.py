import uuid
from collections.abc import Sequence
from datetime import date
from typing import Any, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String as SAString, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.value_objects.aliases import normalize_aliases
from src.infrastructure.db.models.base import BaseInfrastructureModel
from src.infrastructure.db.models.music import (
    AlbumModel,
    ArtistModel,
    EventModel,
    FranchiseModel,
)
from src.infrastructure.db.session import get_async_database_session
from src.presentation.api.dependencies import get_current_active_user, get_current_superuser
from src.presentation.schemas.entities import (
    ArtistCreateSchema,
    ArtistResponseSchema,
    EventCreateSchema,
    EventResponseSchema,
    EventUpdateSchema,
    FranchiseCreateSchema,
    FranchiseResponseSchema,
    PaginatedEventsResponseSchema,
)


router = APIRouter(prefix="/entities", tags=["Master Entity Registry"])

ModelT = TypeVar("ModelT", bound=BaseInfrastructureModel)


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


async def _search_master_entities(
    session: AsyncSession,
    model_cls: type[ModelT],
    query: str,
    limit: int,
    search_columns: list[Any],
    order_column: Any,
) -> Sequence[ModelT]:
    stmt = select(model_cls)
    q = query.strip()
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(*[col.ilike(pattern) for col in search_columns]))
    stmt = stmt.order_by(order_column).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def _get_distinct_album_attribute(
    session: AsyncSession,
    column: Any,
    query: str,
    limit: int = 20,
) -> list[str]:
    stmt = select(column).where(column.is_not(None)).distinct()
    q = query.strip()
    if q:
        stmt = stmt.where(column.ilike(f"%{q}%"))
    stmt = stmt.order_by(column).limit(limit)
    res = await session.execute(stmt)
    return [r for r in res.scalars().all() if r]


def _merge_aliases(existing: list[str] | None, incoming: list[str]) -> list[str]:
    merged = list(existing or [])
    seen = {a.casefold() for a in merged}
    for alias in normalize_aliases(incoming):
        if alias.casefold() not in seen:
            merged.append(alias)
            seen.add(alias.casefold())
    return merged


async def _get_or_create_named_entity(
    session: AsyncSession,
    model_cls: type[ModelT],
    name_original: str,
    incoming_aliases: list[str],
    **extra_fields: Any,
) -> ModelT:
    clean_name = name_original.strip()
    aliases = normalize_aliases(incoming_aliases)

    stmt = select(model_cls).where(model_cls.name_original.ilike(clean_name)).limit(1)
    res = await session.execute(stmt)
    existing = res.scalars().first()

    if existing:
        existing.aliases = _merge_aliases(existing.aliases, aliases)
        await session.commit()
        await session.refresh(existing)
        return existing

    new_entity = model_cls(
        id=uuid.uuid4(),
        name_original=clean_name,
        aliases=aliases,
        **extra_fields,
    )
    session.add(new_entity)
    await session.commit()
    await session.refresh(new_entity)
    return new_entity


@router.get("/artists", response_model=list[ArtistResponseSchema])
async def search_artists(
    query: str = Query(default="", description="Search query for artist name or alias"),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _search_master_entities(
        session=session,
        model_cls=ArtistModel,
        query=query,
        limit=limit,
        search_columns=[
            ArtistModel.name_original,
            cast(ArtistModel.aliases, SAString),
        ],
        order_column=ArtistModel.name_original,
    )


@router.post(
    "/artists",
    response_model=ArtistResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_artist(
    payload: ArtistCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _superuser=Depends(get_current_superuser),
):
    return await _get_or_create_named_entity(
        session=session,
        model_cls=ArtistModel,
        name_original=payload.name_original,
        incoming_aliases=payload.aliases,
    )


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
    _user=Depends(get_current_active_user),
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
    _user=Depends(get_current_active_user),
):
    stmt = select(EventModel).where(EventModel.id == event_id)
    res = await session.execute(stmt)
    event = res.scalars().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )
    return event


@router.post(
    "/events",
    response_model=EventResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    payload: EventCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _superuser=Depends(get_current_superuser),
):
    stmt = (
        select(EventModel).where(EventModel.short_name.ilike(payload.short_name.strip())).limit(1)
    )
    res = await session.execute(stmt)
    existing = res.scalars().first()
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
    _superuser=Depends(get_current_superuser),
):
    stmt = select(EventModel).where(EventModel.id == event_id)
    res = await session.execute(stmt)
    event = res.scalars().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )

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
    _superuser=Depends(get_current_superuser),
):
    stmt = select(EventModel).where(EventModel.id == event_id)
    res = await session.execute(stmt)
    event = res.scalars().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with ID '{event_id}' was not found.",
        )

    await session.delete(event)
    await session.commit()


@router.get("/franchises", response_model=list[FranchiseResponseSchema])
async def search_franchises(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _search_master_entities(
        session=session,
        model_cls=FranchiseModel,
        query=query,
        limit=limit,
        search_columns=[
            FranchiseModel.name_original,
            cast(FranchiseModel.aliases, SAString),
        ],
        order_column=FranchiseModel.name_original,
    )


@router.post(
    "/franchises",
    response_model=FranchiseResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_franchise(
    payload: FranchiseCreateSchema,
    session: AsyncSession = Depends(get_async_database_session),
    _superuser=Depends(get_current_superuser),
):
    return await _get_or_create_named_entity(
        session=session,
        model_cls=FranchiseModel,
        name_original=payload.name_original,
        incoming_aliases=payload.aliases,
        franchise_type=payload.franchise_type,
    )


@router.get("/labels", response_model=list[str])
async def get_distinct_labels(
    query: str = Query(default=""),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _get_distinct_album_attribute(session, AlbumModel.label, query)


@router.get("/publishers", response_model=list[str])
async def get_distinct_publishers(
    query: str = Query(default=""),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _get_distinct_album_attribute(session, AlbumModel.publisher, query)
