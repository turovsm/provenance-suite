from pydantic import BaseModel, ConfigDict, Field


class UserLoginRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    email: str = Field(
        ...,
        max_length=255,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    password: str = Field(..., min_length=12, max_length=128)


class RefreshTokenRequestSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    refresh_token: str = Field(..., min_length=10)


class TokenResponseSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
