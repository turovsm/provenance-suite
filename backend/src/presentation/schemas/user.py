import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str = Field(
        ...,
        description="Primary authentication handle for the identity account.",
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )

    password: str = Field(
        ...,
        description="Plaintext password string meeting baseline system entropy minimums.",
        min_length=12,
        max_length=128,
    )


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
