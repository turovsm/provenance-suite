from enum import StrEnum
from pathlib import Path

from pydantic import Field, PostgresDsn, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(StrEnum):
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

    ENVIRONMENT: EnvironmentType = Field(default=EnvironmentType.DEVELOPMENT)

    APP_PORT: int = Field(default=8088, description="Main gateway public port")
    BACKEND_PORT: int = Field(default=8000, description="API server port")
    FRONTEND_PORT: int = Field(default=4200, description="Dev frontend SPA port")

    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="127.0.0.1")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="provenance_vault")
    DATABASE_URL: PostgresDsn = None

    REDIS_HOST: str = Field(default="127.0.0.1")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    MINIO_ENDPOINT: str = Field(default="127.0.0.1:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadminpassword")
    MINIO_BUCKET_NAME: str = Field(default="provenance-covers")
    MINIO_SECURE: bool = Field(default=False)
    MINIO_PUBLIC_BASE_URL: str = Field(
        default="http://localhost:8088/provenance-covers",
        description="Public S3 CDN endpoint for direct cover downloads.",
    )

    SECURITY_PEPPER: str = Field(min_length=32)
    JWT_SECRET_KEY: str = Field(min_length=64)
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    MAX_UPLOAD_SIZE_BYTES: int = Field(default=10_485_760, description="10MB payload max limit")

    BACKUP_BUCKET_NAME: str = Field(
        default="provenance-backups",
        description="Private MinIO bucket receiving scheduled pg_dump archives.",
    )
    BACKUP_RETENTION_COUNT: int = Field(
        default=14, description="Number of most recent database dumps to retain."
    )
    BACKUP_CRON_HOUR: int = Field(default=3, description="UTC hour for the nightly dump job.")

    RATE_LIMIT_AUTH_PER_MIN: int = Field(default=10)
    RATE_LIMIT_MUTATION_PER_MIN: int = Field(default=30)
    RATE_LIMIT_READ_PER_MIN: int = Field(default=300)
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_async_database_dsn(cls, v: str | None, info: ValidationInfo) -> PostgresDsn:
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

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = AppSettings()
