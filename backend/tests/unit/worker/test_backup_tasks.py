import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import Path as AsyncPath

from src.infrastructure.worker.tasks import (
    LOGICAL_BACKUP_PREFIX,
    cold_logical_dump,
    compute_file_sha256,
    physical_base_backup,
    prune_logical_dumps,
)


@pytest.mark.asyncio
async def test_compute_file_sha256(tmp_path: Path) -> None:
    test_file = AsyncPath(tmp_path) / "sample.bin"
    content = b"Provenance Archival Audio Stream Payload" * 5000
    await test_file.write_bytes(content)

    expected_digest = hashlib.sha256(content).hexdigest()
    computed_digest = await compute_file_sha256(Path(test_file))

    assert computed_digest == expected_digest


@pytest.mark.asyncio
async def test_cold_logical_dump_success_and_cleanup(tmp_path: Path) -> None:
    mock_storage = MagicMock()
    mock_storage.upload_backup_file = AsyncMock(return_value="s3_key")
    mock_storage.list_backup_objects = AsyncMock(return_value=[])
    mock_storage.delete_cover = AsyncMock()

    with (
        patch("src.infrastructure.worker.tasks.ensure_temp_dir", return_value=tmp_path),
        patch(
            "src.infrastructure.worker.tasks.MinioObjectStorageService", return_value=mock_storage
        ),
        patch("asyncio.create_subprocess_exec") as mock_proc,
    ):

        async def mock_dump_exec(*args: Any, **_kwargs: Any) -> AsyncMock:
            for idx, arg in enumerate(args):
                if arg == "--file":
                    dump_file = AsyncPath(args[idx + 1])
                    await dump_file.write_bytes(b"PGDUMP_BINARY_DATA")
            mock_res = AsyncMock()
            mock_res.communicate.return_value = (b"", b"")
            mock_res.returncode = 0
            return mock_res

        mock_proc.side_effect = mock_dump_exec

        result_key = await cold_logical_dump({})

        assert result_key.startswith(LOGICAL_BACKUP_PREFIX)
        assert result_key.endswith(".dump")
        assert mock_storage.upload_backup_file.await_count == 2

        # Verify disk files are cleaned up asynchronously
        async_tmp = AsyncPath(tmp_path)
        dump_files = [p async for p in async_tmp.glob("*.dump")]
        sha_files = [p async for p in async_tmp.glob("*.sha256")]
        assert len(dump_files) == 0
        assert len(sha_files) == 0


@pytest.mark.asyncio
async def test_cold_logical_dump_failure_cleans_up_disk(tmp_path: Path) -> None:
    mock_storage = MagicMock()

    with (
        patch("src.infrastructure.worker.tasks.ensure_temp_dir", return_value=tmp_path),
        patch(
            "src.infrastructure.worker.tasks.MinioObjectStorageService", return_value=mock_storage
        ),
        patch("asyncio.create_subprocess_exec") as mock_proc,
    ):
        mock_res = AsyncMock()
        mock_res.communicate.return_value = (b"", b"FATAL: Database connection rejected")
        mock_res.returncode = 1
        mock_proc.return_value = mock_res

        with pytest.raises(RuntimeError, match="pg_dump failed with exit code 1"):
            await cold_logical_dump({})

        # Filesystem must remain clean on failure
        async_tmp = AsyncPath(tmp_path)
        remaining = [p async for p in async_tmp.iterdir()]
        assert len(remaining) == 0


@pytest.mark.asyncio
async def test_physical_base_backup_success() -> None:
    with patch("asyncio.create_subprocess_exec") as mock_proc:
        mock_res = AsyncMock()
        mock_res.communicate.return_value = (b"SUCCESS", b"")
        mock_res.returncode = 0
        mock_proc.return_value = mock_res

        result = await physical_base_backup({})

        assert "complete" in result.lower()
        assert mock_proc.call_count == 2
        first_call_args = mock_proc.call_args_list[0][0]
        second_call_args = mock_proc.call_args_list[1][0]

        assert first_call_args[:2] == ("wal-g", "backup-push")
        assert second_call_args == ("wal-g", "delete", "retain", "FULL", "4", "--confirm")


@pytest.mark.asyncio
async def test_physical_base_backup_raises_on_failure() -> None:
    with patch("asyncio.create_subprocess_exec") as mock_proc:
        mock_res = AsyncMock()
        mock_res.communicate.return_value = (b"", b"WAL-G S3 bucket authentication failed")
        mock_res.returncode = 2
        mock_proc.return_value = mock_res

        with pytest.raises(RuntimeError, match="WAL-G base backup failed"):
            await physical_base_backup({})


@pytest.mark.asyncio
async def test_prune_logical_dumps_retention_fifo() -> None:
    mock_storage = MagicMock()
    mock_storage.list_backup_objects = AsyncMock(
        return_value=[
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-01T040000Z.dump",
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-01T040000Z.dump.sha256",
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-02T040000Z.dump",
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-02T040000Z.dump.sha256",
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-03T040000Z.dump",
            f"{LOGICAL_BACKUP_PREFIX}db_2026-08-03T040000Z.dump.sha256",
        ]
    )
    mock_storage.delete_cover = AsyncMock()

    await prune_logical_dumps(mock_storage, keep=2)

    deleted_keys = [call[0][0] for call in mock_storage.delete_cover.call_args_list]
    assert f"{LOGICAL_BACKUP_PREFIX}db_2026-08-01T040000Z.dump" in deleted_keys
    assert f"{LOGICAL_BACKUP_PREFIX}db_2026-08-01T040000Z.dump.sha256" in deleted_keys
    assert len(deleted_keys) == 2
