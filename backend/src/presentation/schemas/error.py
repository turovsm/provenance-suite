from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetailSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Machine-readable snake_case error code.")
    message: str = Field(..., description="Human-readable error description.")
    details: Any | None = Field(
        default=None, description="Optional diagnostic details or validation items."
    )


class ErrorResponseEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str = Field(default="error", description="Response status tag.")
    error: ErrorDetailSchema
