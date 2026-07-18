from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # System Environment Definition
    ENVIRONMENT: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT)

    # Asynchronous Core Data Persistence Routing
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="127.0.0.1")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="provenance_vault")
    DATABASE_URL: Optional[PostgresDsn] = None

    # Cryptographic & Identity Security Enclaves
    SECURITY_PEPPER: str = Field(min_length=32, description="System-wide static argon2 pepper.")
    JWT_SECRET_KEY: str = Field(min_length=64, description="Symmetric payload authorization key.")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_database_dsn(cls, v: Optional[str], info: ValidationInfo) -> PostgresDsn:
        if isinstance(v, str) and v:
            return PostgresDsn(v)

        data = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_HOST"),
            port=data.get("POSTGRES_PORT"),
            path=data.get("POSTGRES_DB"),
        )


settings = AppSettings()