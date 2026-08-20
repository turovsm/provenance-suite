import uuid
from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import Text, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.db.models.base import BaseInfrastructureModel
from src.infrastructure.db.models.music import AlbumModel


ModelT = TypeVar("ModelT", bound=BaseInfrastructureModel)


async def get_entity_or_404(
    session: AsyncSession,
    model_cls: type[ModelT],
    entity_id: uuid.UUID,
    entity_name: str,
) -> ModelT:
    stmt = select(model_cls).where(model_cls.id == entity_id)
    res = await session.execute(stmt)
    entity = res.scalars().first()
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found.",
        )
    return entity


async def search_named_entities(
    session: AsyncSession,
    model_cls: type[ModelT],
    query: str = "",
    limit: int = 20,
) -> list[ModelT]:
    stmt = select(model_cls)
    q = query.strip()
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                model_cls.name_original.ilike(pattern),
                cast(model_cls.aliases, Text).ilike(pattern),
            )
        )
    stmt = stmt.order_by(model_cls.name_original).limit(limit)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def fetch_albums_by_entity_fk(
    session: AsyncSession,
    fk_column: Any,
    entity_id: uuid.UUID,
) -> list[AlbumModel]:
    stmt = (
        select(AlbumModel)
        .where(fk_column == entity_id)
        .options(
            selectinload(AlbumModel.covers),
            selectinload(AlbumModel.album_artist),
            selectinload(AlbumModel.label),
            selectinload(AlbumModel.publisher),
            selectinload(AlbumModel.discs),
        )
        .order_by(AlbumModel.release_date_sort.desc().nulls_last())
    )
    res = await session.execute(stmt)
    return list(res.unique().scalars().all())


async def find_existing_entity_by_name(
    session: AsyncSession,
    model_cls: type[ModelT],
    name: str,
    name_attr: str = "name_original",
) -> ModelT | None:
    clean_name = name.strip()
    col = getattr(model_cls, name_attr)
    stmt = select(model_cls).where(col.ilike(clean_name)).limit(1)
    res = await session.execute(stmt)
    return res.scalars().first()
