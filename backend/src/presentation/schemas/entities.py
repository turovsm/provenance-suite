import uuid
from datetime import datetime

from pydantic import Base64Bytes, BaseModel, ConfigDict, Field

from src.domain import MAX_ALIAS_LENGTH, MAX_ALIASES_PER_ENTITY


class ArtistCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class ArtistUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str | None = Field(default=None, min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] | None = Field(default=None, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class ArtistResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    image_url: str | None = None
    description: str | None = None
    created_at: datetime | None = None


class FranchiseCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    franchise_type: str = Field(default="Game", max_length=128)
    description: str | None = None
    image_data: Base64Bytes | None = None


class FranchiseUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str | None = Field(default=None, min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] | None = Field(default=None, max_length=MAX_ALIASES_PER_ENTITY)
    franchise_type: str | None = Field(default=None, max_length=128)
    description: str | None = None
    image_data: Base64Bytes | None = None


class FranchiseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    franchise_type: str
    image_url: str | None = None
    description: str | None = None
    created_at: datetime | None = None


class LabelCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class LabelUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str | None = Field(default=None, min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] | None = Field(default=None, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class LabelResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    image_url: str | None = None
    description: str | None = None
    created_at: datetime | None = None


class PublisherCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] = Field(default_factory=list, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class PublisherUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str | None = Field(default=None, min_length=1, max_length=MAX_ALIAS_LENGTH)
    aliases: list[str] | None = Field(default=None, max_length=MAX_ALIASES_PER_ENTITY)
    description: str | None = None
    image_data: Base64Bytes | None = None


class PublisherResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    image_url: str | None = None
    description: str | None = None
    created_at: datetime | None = None


class EntitySummarySchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: uuid.UUID
    name_original: str
    aliases: list[str] = Field(default_factory=list)
    entity_type: str  # "artist", "franchise", "label", "publisher"
    image_url: str | None = None
    description: str | None = None
    franchise_type: str | None = None
    created_at: datetime | None = None


class PaginatedEntitiesResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EntitySummarySchema]
    total_count: int
    limit: int
    offset: int


class EventDateRangeSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    start_date: str | None = None
    end_date: str | None = None


class EventCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_name: str = Field(..., min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=512)
    start_date: str | None = None
    end_date: str | None = None
    original_start_date: str | None = None
    original_end_date: str | None = None
    date_history: list[EventDateRangeSchema] = Field(default_factory=list)
    additional_dates: list[EventDateRangeSchema] = Field(default_factory=list)
    status: str = Field(default="HELD", max_length=32)


class EventUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_name: str | None = Field(default=None, min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=512)
    start_date: str | None = None
    end_date: str | None = None
    original_start_date: str | None = None
    original_end_date: str | None = None
    date_history: list[EventDateRangeSchema] | None = None
    additional_dates: list[EventDateRangeSchema] | None = None
    status: str | None = Field(default=None, max_length=32)


class EventResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    short_name: str
    full_name: str | None
    start_date: str | None
    end_date: str | None
    original_start_date: str | None
    original_end_date: str | None
    date_history: list[EventDateRangeSchema] = Field(default_factory=list)
    additional_dates: list[EventDateRangeSchema] = Field(default_factory=list)
    status: str


class PaginatedEventsResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[EventResponseSchema]
    total_count: int
    limit: int
    offset: int
