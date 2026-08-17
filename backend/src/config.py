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

    # Network Ports & Gateways
    APP_PORT: int = Field(default=8088, description="Main gateway public port")
    BACKEND_PORT: int = Field(default=8000, description="API server port")
    FRONTEND_PORT: int = Field(default=4200, description="Dev frontend SPA port")
    CORS_ORIGINS: str = Field(
        default="http://127.0.0.1:4200,http://localhost:4200,http://127.0.0.1:8088,http://localhost:8088",
        description="Comma-separated list of allowed CORS origins",
    )

    # PostgreSQL Configuration
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_HOST: str = Field(default="127.0.0.1")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="provenance_vault")
    DATABASE_URL: PostgresDsn = None

    # Database Connection Pool Tuning
    DB_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_RECYCLE_SECONDS: int = Field(default=1800, ge=60)
    DB_COMMAND_TIMEOUT_SECONDS: float = Field(default=30.0, ge=1.0)

    # Redis Configuration
    REDIS_HOST: str = Field(default="127.0.0.1")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    # MinIO S3 Object Storage
    MINIO_ENDPOINT: str = Field(default="127.0.0.1:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadminpassword")
    MINIO_BUCKET_NAME: str = Field(default="provenance-covers")
    MINIO_SECURE: bool = Field(default=False)
    MINIO_PUBLIC_BASE_URL: str = Field(
        default="http://localhost:8088/provenance-covers",
        description="Public S3 CDN endpoint for direct cover downloads.",
    )

    # Image Processing & Media Compression
    COVER_IMAGE_MAX_DIMENSION: int = Field(default=500, ge=100, le=4000)
    ENTITY_IMAGE_MAX_DIMENSION: int = Field(default=800, ge=100, le=4000)
    IMAGE_JPEG_QUALITY: int = Field(default=85, ge=1, le=100)

    # Cryptographic Tokens & Argon2 Hashing
    SECURITY_PEPPER: str = Field(min_length=32)
    JWT_SECRET_KEY: str = Field(min_length=64)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_LEEWAY_SECONDS: int = Field(default=30, ge=0, le=300)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    ARGON2_TIME_COST: int = Field(default=3, ge=1, le=10)
    ARGON2_MEMORY_COST_KIB: int = Field(default=65536, ge=8192)
    ARGON2_PARALLELISM: int = Field(default=4, ge=1, le=16)

    # Request & Rate Limits
    MAX_UPLOAD_SIZE_BYTES: int = Field(default=10_485_760, description="10MB payload max limit")
    RATE_LIMIT_AUTH_PER_MIN: int = Field(default=10)
    RATE_LIMIT_MUTATION_PER_MIN: int = Field(default=30)
    RATE_LIMIT_READ_PER_MIN: int = Field(default=300)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # Backup & Disaster Recovery Architecture (Hybrid Strategy)
    BACKUP_BUCKET_NAME: str = Field(default="provenance-backups")
    BACKUP_TMP_DIR: str = Field(default="/tmp/provenance_backups")
    BACKUP_LOGICAL_RETENTION_COUNT: int = Field(
        default=8, description="Retain 8 logical dumps (4 months of bi-weekly fail-safes)"
    )
    WALG_BASE_BACKUP_RETENTION_COUNT: int = Field(
        default=4, description="Retain 4 full weekly physical snapshots"
    )
    WALG_COMPRESSION_METHOD: str = Field(
        default="zstd", description="Compression algorithm for WAL-G: zstd, lz4, or gzip"
    )

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
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def walg_s3_prefix(self) -> str:
        return f"s3://{self.BACKUP_BUCKET_NAME}/wal-g"


settings = AppSettings()
