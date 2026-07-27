import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Public display name handle.",
    )
    email: str = Field(
        ...,
        description="Primary authentication handle for the account.",
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    password: str = Field(
        ...,
        description="Plaintext password string.",
        min_length=12,
        max_length=128,
    )


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
