import asyncio
import hashlib
import logging
from datetime import UTC, datetime
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from src.config import settings
from src.infrastructure.storage.object_storage import MinioObjectStorageService


logger = logging.getLogger("provenance.worker")

BACKUP_PREFIX = "postgres/"


async def compute_archive_sha256(_ctx: dict[Any, Any], archive_id: str, file_bytes: bytes) -> str:
    logger.info("Starting SHA256 calculation for archive: %s", archive_id)
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    digest = hasher.hexdigest()
    logger.info("SHA256 for archive %s: %s", archive_id, digest)
    return digest


async def run_pg_dump() -> bytes:
    process = await asyncio.create_subprocess_exec(
        "pg_dump",
        "--host",
        settings.POSTGRES_HOST,
        "--port",
        str(settings.POSTGRES_PORT),
        "--username",
        settings.POSTGRES_USER,
        "--dbname",
        settings.POSTGRES_DB,
        "--format",
        "custom",
        "--no-password",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PGPASSWORD": settings.POSTGRES_PASSWORD},
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(
            f"pg_dump exited with code {process.returncode}: {stderr.decode(errors='replace')}"
        )
    if not stdout:
        raise RuntimeError("pg_dump produced an empty archive; aborting upload.")

    return stdout


async def backup_database(_ctx: dict[Any, Any]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    object_key = f"{BACKUP_PREFIX}{settings.POSTGRES_DB}-{timestamp}.dump"

    logger.info("Starting scheduled database backup -> %s", object_key)
    dump_bytes = await run_pg_dump()

    storage = MinioObjectStorageService()
    await storage.upload_backup(object_key, dump_bytes)
    logger.info("Backup uploaded (%.2f MiB): %s", len(dump_bytes) / 1_048_576, object_key)

    pruned = await storage.prune_backups(prefix=BACKUP_PREFIX, keep=settings.BACKUP_RETENTION_COUNT)
    if pruned:
        logger.info("Pruned %d stale backup(s): %s", len(pruned), ", ".join(pruned))

    return object_key


class WorkerSettings:
    functions = [compute_archive_sha256, backup_database]
    cron_jobs = [
        cron(
            backup_database,
            hour=settings.BACKUP_CRON_HOUR,
            minute=0,
            timeout=600,
            max_tries=1,
        ),
    ]
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
