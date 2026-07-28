import uuid
from collections.abc import Sequence
from typing import Any, TypeVar

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
    FranchiseCreateSchema,
    FranchiseResponseSchema,
)


router = APIRouter(prefix="/entities", tags=["Master Entity Registry"])

ModelT = TypeVar("ModelT", bound=BaseInfrastructureModel)


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


@router.get("/artists", response_model=list[ArtistResponseSchema])
async def search_artists(
    query: str = Query(default="", description="Search query for artist or circle name"),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _search_master_entities(
        session=session,
        model_cls=ArtistModel,
        query=query,
        limit=limit,
        search_columns=[ArtistModel.name_original, ArtistModel.name_translated],
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
    stmt = (
        select(ArtistModel)
        .where(ArtistModel.name_original.ilike(payload.name_original.strip()))
        .limit(1)
    )
    res = await session.execute(stmt)
    existing = res.scalars().first()

    if payload.name_translated and payload.name_translated.strip():
        translated_name = payload.name_translated.strip()
    else:
        translated_name = None

    if existing:
        existing.name_translated = translated_name
        await session.commit()
        await session.refresh(existing)
        return existing

    new_artist = ArtistModel(
        id=uuid.uuid4(),
        name_original=payload.name_original.strip(),
        name_translated=translated_name,
    )
    session.add(new_artist)
    await session.commit()
    await session.refresh(new_artist)
    return new_artist


@router.get("/events", response_model=list[EventResponseSchema])
async def search_events(
    query: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_database_session),
    _user=Depends(get_current_active_user),
):
    return await _search_master_entities(
        session=session,
        model_cls=EventModel,
        query=query,
        limit=limit,
        search_columns=[EventModel.short_name, EventModel.full_name],
        order_column=EventModel.short_name,
    )


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

    new_event = EventModel(
        id=uuid.uuid4(),
        short_name=payload.short_name.strip(),
        full_name=payload.full_name.strip() if payload.full_name else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
    )
    session.add(new_event)
    await session.commit()
    await session.refresh(new_event)
    return new_event


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
        search_columns=[FranchiseModel.name_original, FranchiseModel.name_translated],
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
    stmt = (
        select(FranchiseModel)
        .where(FranchiseModel.name_original.ilike(payload.name_original.strip()))
        .limit(1)
    )
    res = await session.execute(stmt)
    existing = res.scalars().first()
    if existing:
        return existing

    new_franchise = FranchiseModel(
        id=uuid.uuid4(),
        name_original=payload.name_original.strip(),
        name_translated=payload.name_translated.strip() if payload.name_translated else None,
        franchise_type=payload.franchise_type,
    )
    session.add(new_franchise)
    await session.commit()
    await session.refresh(new_franchise)
    return new_franchise


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
