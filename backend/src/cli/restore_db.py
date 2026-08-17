import argparse
import asyncio
import hashlib
import logging
import os
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import settings
from src.infrastructure.storage.object_storage import MinioObjectStorageService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("provenance.cli.restore")

LOGICAL_PREFIX = "logical_dumps/"


def ensure_temp_dir() -> Path:
    tmp_path = Path(settings.BACKUP_TMP_DIR)
    tmp_path.mkdir(parents=True, exist_ok=True)
    return tmp_path


def compute_file_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


async def list_available_backups() -> None:
    storage = MinioObjectStorageService()
    objects = await storage.list_backup_objects(prefix="")

    logical_dumps = sorted(
        [obj for obj in objects if obj.startswith(LOGICAL_PREFIX) and obj.endswith(".dump")],
        reverse=True,
    )
    wal_objects = [obj for obj in objects if obj.startswith("wal-g/")]

    print("\n" + "=" * 70)
    print("PROVENANCE VAULT - AVAILABLE BACKUP MANIFESTS")
    print("=" * 70)

    bucket = settings.BACKUP_BUCKET_NAME
    print(f"\n[1] Cold Logical Dumps (MinIO: s3://{bucket}/{LOGICAL_PREFIX})")
    if not logical_dumps:
        print("\t(No cold logical dumps found)")
    else:
        for idx, dump in enumerate(logical_dumps, start=1):
            has_sha = f"{dump}.sha256" in objects
            sha_status = "SHA256 Manifest: OK" if has_sha else "SHA256 Manifest: MISSING"
            print(f"\t{idx:02d}. {dump:<50} [{sha_status}]")

    print(f"\n[2] Continuous WAL-G Physical Stream (MinIO: {settings.walg_s3_prefix})")
    base_backups = [obj for obj in wal_objects if "basebackups_" in obj]
    wal_segments = [obj for obj in wal_objects if "wal_" in obj]
    print(f"\t- Base Backup Snapshots : {len(base_backups)}")
    print(f"\t- Archived WAL Segments : {len(wal_segments)}")
    print("=" * 70 + "\n")


async def download_backup_file(object_key: str, destination_path: Path) -> None:
    storage = MinioObjectStorageService()
    logger.info(
        "Downloading s3://%s/%s -> %s",
        settings.BACKUP_BUCKET_NAME,
        object_key,
        destination_path,
    )
    await storage.download_backup_file(object_key, destination_path)


async def verify_dump_checksum(dump_key: str) -> tuple[bool, str, str]:
    tmp_dir = ensure_temp_dir()
    dump_filename = Path(dump_key).name
    checksum_filename = f"{dump_filename}.sha256"

    local_dump = tmp_dir / dump_filename
    local_checksum = tmp_dir / checksum_filename

    try:
        await download_backup_file(dump_key, local_dump)
        await download_backup_file(f"{dump_key}.sha256", local_checksum)

        expected_sha_raw = local_checksum.read_text(encoding="utf-8").strip()
        expected_sha = expected_sha_raw.split()[0]
        computed_sha = compute_file_sha256(local_dump)

        is_valid = computed_sha.lower() == expected_sha.lower()
        return is_valid, computed_sha, expected_sha
    finally:
        if local_dump.exists():
            local_dump.unlink()
        if local_checksum.exists():
            local_checksum.unlink()


async def restore_logical_dump(
    target_key: str | None = None,
    jobs: int = 4,
    clean: bool = True,
    dry_run_verify: bool = False,
) -> None:
    storage = MinioObjectStorageService()
    all_objects = await storage.list_backup_objects(prefix=LOGICAL_PREFIX)
    dump_candidates = sorted([k for k in all_objects if k.endswith(".dump")], reverse=True)

    if not dump_candidates:
        logger.error("No logical dump files found in bucket '%s'.", settings.BACKUP_BUCKET_NAME)
        sys.exit(1)

    chosen_key = target_key or dump_candidates[0]
    if chosen_key not in dump_candidates:
        logger.error("Requested backup key '%s' does not exist.", chosen_key)
        sys.exit(1)

    logger.info("Selected backup candidate: %s", chosen_key)

    tmp_dir = ensure_temp_dir()
    dump_filename = Path(chosen_key).name
    checksum_filename = f"{dump_filename}.sha256"

    local_dump = tmp_dir / dump_filename
    local_checksum = tmp_dir / checksum_filename

    try:
        logger.info("Step 1/3: Fetching archive and manifest from MinIO...")
        await download_backup_file(chosen_key, local_dump)
        await download_backup_file(f"{chosen_key}.sha256", local_checksum)

        logger.info("Step 2/3: Verifying SHA-256 cryptographic checksum...")
        expected_sha = local_checksum.read_text(encoding="utf-8").strip().split()[0]
        computed_sha = compute_file_sha256(local_dump)

        if computed_sha.lower() != expected_sha.lower():
            logger.critical(
                "CHECKSUM INTEGRITY MISMATCH!\nExpected: %s\nComputed: %s",
                expected_sha,
                computed_sha,
            )
            sys.exit(1)

        logger.info("Checksum verified OK [%s]", computed_sha)

        if dry_run_verify:
            logger.info("Dry-run verification completed. Skipping restore.")
            return

        logger.info("Step 3/3: Executing parallel pg_restore (%d worker jobs)...", jobs)
        cmd = [
            "pg_restore",
            "--host",
            settings.POSTGRES_HOST,
            "--port",
            str(settings.POSTGRES_PORT),
            "--username",
            settings.POSTGRES_USER,
            "--dbname",
            settings.POSTGRES_DB,
            "--jobs",
            str(jobs),
            "--no-password",
            "--verbose",
        ]
        if clean:
            cmd.extend(["--clean", "--if-exists"])
        cmd.append(str(local_dump))

        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        _, stderr = await process.communicate()

        if process.returncode not in (0, 1):
            err_output = stderr.decode(errors="replace")
            logger.error("pg_restore failed with exit code %d:\n%s", process.returncode, err_output)
            sys.exit(process.returncode)

        logger.info("Database restoration completed successfully.")

    finally:
        if local_dump.exists():
            local_dump.unlink()
        if local_checksum.exists():
            local_checksum.unlink()


def generate_pitr_recovery_config(pgdata_dir: Path, target_time: str | None = None) -> None:
    if not pgdata_dir.exists():
        logger.error("PGDATA directory '%s' does not exist.", pgdata_dir)
        sys.exit(1)

    signal_file = pgdata_dir / "recovery.signal"
    conf_file = pgdata_dir / "postgresql.auto.conf"

    logger.info("Creating %s...", signal_file)
    signal_file.touch(exist_ok=True)

    config_lines = [
        "\n# --- Automated WAL-G PITR Recovery Configuration ---",
        "restore_command = 'wal-g wal-fetch %f %p'",
        "recovery_target_action = 'promote'",
    ]
    if target_time:
        config_lines.append(f"recovery_target_time = '{target_time}'")

    with conf_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(config_lines) + "\n")

    logger.info("Recovery configuration appended to %s", conf_file)
    print("\n" + "=" * 70)
    print("WAL-G PITR CONFIGURATION READY")
    print(f" Target PGDATA : {pgdata_dir}")
    print(f" Target Time   : {target_time or 'LATEST (Replay all WAL)'}")
    print(" Next Step     : Start the postgres container to begin continuous WAL replay.")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Provenance Disaster Recovery & Backup CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "list",
        help="List all logical dumps and physical WAL-G backups in MinIO",
    )

    logical_parser = subparsers.add_parser(
        "restore-logical",
        help="Restore database from a cold .dump file",
    )
    logical_parser.add_argument(
        "--key",
        default=None,
        help="Specific S3 key to restore (default: latest)",
    )
    logical_parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Number of parallel pg_restore worker threads",
    )
    logical_parser.add_argument(
        "--no-clean",
        dest="clean",
        action="store_false",
        help="Do not drop existing objects before restoring",
    )
    logical_parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Download and verify SHA256 checksum without restoring",
    )

    verify_parser = subparsers.add_parser(
        "verify-checksum",
        help="Verify SHA256 checksum integrity of an S3 dump",
    )
    verify_parser.add_argument("key", help="S3 object key of the .dump file")

    pitr_parser = subparsers.add_parser(
        "prep-pitr",
        help="Configure PostgreSQL directory for WAL-G PITR",
    )
    pitr_parser.add_argument(
        "--pgdata",
        type=Path,
        default=Path("/var/lib/postgresql/data"),
        help="Path to $PGDATA directory",
    )
    pitr_parser.add_argument(
        "--target-time",
        default=None,
        help="Target recovery time (e.g. '2026-08-14 14:30:00 UTC')",
    )

    args = parser.parse_args()

    if args.command == "list":
        asyncio.run(list_available_backups())
    elif args.command == "restore-logical":
        asyncio.run(
            restore_logical_dump(
                target_key=args.key,
                jobs=args.jobs,
                clean=args.clean,
                dry_run_verify=args.verify_only,
            )
        )
    elif args.command == "verify-checksum":
        is_valid, comp, exp = asyncio.run(verify_dump_checksum(args.key))
        if is_valid:
            print(f"[OK] Checksum match: {comp}")
        else:
            print(f"[FAILED] Mismatch!\nComputed: {comp}\nExpected: {exp}")
            sys.exit(1)
    elif args.command == "prep-pitr":
        generate_pitr_recovery_config(args.pgdata, args.target_time)


if __name__ == "__main__":
    main()
