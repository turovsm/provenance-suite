import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.domain import MAX_ALIAS_LENGTH, MAX_ALIASES_PER_ENTITY


class ArtistCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(
        default_factory=list,
        max_length=MAX_ALIASES_PER_ENTITY,
        description="Alternative names: romanizations, former names, circle names, etc.",
    )


class ArtistResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class EventCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_name: str = Field(..., min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=512)
    start_date: date | None = None
    end_date: date | None = None
    status: str = Field(default="HELD", max_length=32)


class EventUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_name: str | None = Field(default=None, min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=512)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=32)


class EventResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    short_name: str
    full_name: str | None
    start_date: date | None
    end_date: date | None
    status: str


class FranchiseCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    franchise_type: str = Field(default="Game", max_length=128)


class FranchiseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    franchise_type: str
