import asyncio
import hashlib
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from src.config import settings
from src.infrastructure.storage.object_storage import MinioObjectStorageService


logger = logging.getLogger("provenance.worker")

LOGICAL_BACKUP_PREFIX = "logical_dumps/"


def ensure_temp_dir() -> Path:
    tmp_path = Path(settings.BACKUP_TMP_DIR)
    tmp_path.mkdir(parents=True, exist_ok=True)
    return tmp_path


async def compute_file_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


async def compute_archive_sha256(_ctx: dict[Any, Any], archive_id: str, file_bytes: bytes) -> str:
    logger.info("Computing SHA256 hash for ingested release archive: %s", archive_id)
    return hashlib.sha256(file_bytes).hexdigest()


async def physical_base_backup(_ctx: dict[Any, Any]) -> str:
    logger.info("Starting scheduled physical base backup via WAL-G...")

    s3_endpoint = (
        f"http://{settings.MINIO_ENDPOINT}"
        if not settings.MINIO_SECURE
        else f"https://{settings.MINIO_ENDPOINT}"
    )

    env = os.environ.copy()
    env.update(
        {
            "WALG_S3_PREFIX": settings.walg_s3_prefix,
            "AWS_ACCESS_KEY_ID": settings.MINIO_ACCESS_KEY,
            "AWS_SECRET_ACCESS_KEY": settings.MINIO_SECRET_KEY,
            "AWS_ENDPOINT": s3_endpoint,
            "AWS_S3_FORCE_PATH_STYLE": "true",
            "AWS_REGION": "us-east-1",
            "PGHOST": settings.POSTGRES_HOST,
            "PGPORT": str(settings.POSTGRES_PORT),
            "PGUSER": settings.POSTGRES_USER,
            "PGPASSWORD": settings.POSTGRES_PASSWORD,
            "PGDATABASE": settings.POSTGRES_DB,
            "WALG_COMPRESSION_METHOD": settings.WALG_COMPRESSION_METHOD,
        }
    )

    proc = await asyncio.create_subprocess_exec(
        "wal-g",
        "backup-push",
        "/var/lib/postgresql/data",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err_msg = stderr.decode(errors="replace")
        logger.error("WAL-G base backup failed (code %d): %s", proc.returncode, err_msg)
        raise RuntimeError(f"WAL-G base backup failed: {err_msg}")

    logger.info("Physical base backup completed:\n%s", stdout.decode(errors="replace"))

    prune_proc = await asyncio.create_subprocess_exec(
        "wal-g",
        "delete",
        "retain",
        "FULL",
        str(settings.WALG_BASE_BACKUP_RETENTION_COUNT),
        "--confirm",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    p_stdout, p_stderr = await prune_proc.communicate()
    if prune_proc.returncode == 0:
        logger.info("WAL-G retention cleanup executed:\n%s", p_stdout.decode(errors="replace"))
    else:
        logger.warning("WAL-G retention prune warning: %s", p_stderr.decode(errors="replace"))

    return "WAL-G base backup and retention cycle complete."


async def cold_logical_dump(_ctx: dict[Any, Any]) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")
    filename = f"{settings.POSTGRES_DB}_{timestamp}.dump"
    checksum_filename = f"{filename}.sha256"

    tmp_dir = ensure_temp_dir()
    dump_local_path = tmp_dir / filename
    checksum_local_path = tmp_dir / checksum_filename

    dump_s3_key = f"{LOGICAL_BACKUP_PREFIX}{filename}"
    checksum_s3_key = f"{LOGICAL_BACKUP_PREFIX}{checksum_filename}"

    logger.info("Starting streamed cold logical dump -> %s", dump_local_path)

    try:
        proc = await asyncio.create_subprocess_exec(
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
            "--compress",
            "6",
            "--file",
            str(dump_local_path),
            "--no-password",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PGPASSWORD": settings.POSTGRES_PASSWORD},
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            err = stderr.decode(errors="replace")
            raise RuntimeError(f"pg_dump failed with exit code {proc.returncode}: {err}")

        if not dump_local_path.exists() or dump_local_path.stat().st_size == 0:
            raise RuntimeError("pg_dump generated an empty or non-existent dump file.")

        dump_size_mb = dump_local_path.stat().st_size / (1024 * 1024)
        logger.info("Logical dump written to disk (%.2f MB). Computing SHA256...", dump_size_mb)

        sha256_digest = await compute_file_sha256(dump_local_path)
        checksum_local_path.write_text(f"{sha256_digest}  {filename}\n", encoding="utf-8")

        storage = MinioObjectStorageService()
        await storage.upload_backup_file(dump_s3_key, str(dump_local_path))
        await storage.upload_backup_file(
            checksum_s3_key, str(checksum_local_path), content_type="text/plain"
        )
        logger.info("Cold logical dump and manifest uploaded -> %s", dump_s3_key)

        await prune_logical_dumps(storage, keep=settings.BACKUP_LOGICAL_RETENTION_COUNT)

    finally:
        if dump_local_path.exists():
            dump_local_path.unlink()
        if checksum_local_path.exists():
            checksum_local_path.unlink()

    return dump_s3_key


async def prune_logical_dumps(storage: MinioObjectStorageService, keep: int) -> None:
    all_keys = await storage.list_backup_objects(prefix=LOGICAL_BACKUP_PREFIX)
    dump_files = sorted([k for k in all_keys if k.endswith(".dump")], reverse=True)

    stale_dumps = dump_files[keep:]
    for old_dump_key in stale_dumps:
        old_checksum_key = f"{old_dump_key}.sha256"
        logger.info("Pruning expired logical backup: %s", old_dump_key)
        await storage.delete_cover(old_dump_key)
        await storage.delete_cover(old_checksum_key)


class WorkerSettings:
    functions = [
        compute_archive_sha256,
        physical_base_backup,
        cold_logical_dump,
    ]
    cron_jobs = [
        # Weekly Full Physical Base Backup
        cron(
            physical_base_backup,
            weekday=6,
            hour=2,
            minute=0,
            timeout=3600,
            max_tries=1,
            run_at_startup=False,
        ),
        # Bi-Weekly Cold Logical Dump Fail-Safe
        cron(
            cold_logical_dump,
            day={1, 15},
            hour=4,
            minute=0,
            timeout=1800,
            max_tries=1,
            run_at_startup=False,
        ),
    ]
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
    )
