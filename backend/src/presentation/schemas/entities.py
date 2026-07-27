import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ArtistCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name_original: str = Field(..., min_length=1, max_length=512)
    name_translated: str | None = Field(default=None, max_length=512)


class ArtistResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    name_translated: str | None
    created_at: datetime | None = None


class EventCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    short_name: str = Field(..., min_length=1, max_length=128)
    full_name: str | None = Field(default=None, max_length=512)
    start_date: date | None = None
    end_date: date | None = None
    status: str = Field(default="HELD", max_length=32)


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

    name_original: str = Field(..., min_length=1, max_length=512)
    name_translated: str | None = Field(default=None, max_length=512)
    franchise_type: str = Field(default="Game", max_length=128)


class FranchiseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    name_original: str
    name_translated: str | None
    franchise_type: str
