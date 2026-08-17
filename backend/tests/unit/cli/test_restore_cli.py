import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anyio import Path as AsyncPath

from src.cli.restore_db import (
    compute_file_sha256,
    generate_pitr_recovery_config,
    restore_logical_dump,
    verify_dump_checksum,
)


def test_compute_file_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "sample.bin"
    content = b"Provenance Test Payload" * 100
    test_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    assert compute_file_sha256(test_file) == expected


@pytest.mark.asyncio
async def test_verify_dump_checksum_valid(tmp_path: Path) -> None:
    data = b"BACKUP_PAYLOAD"
    digest = hashlib.sha256(data).hexdigest()
    mock_storage = MagicMock()

    with (
        patch("src.cli.restore_db.ensure_temp_dir", return_value=tmp_path),
        patch("src.cli.restore_db.MinioObjectStorageService", return_value=mock_storage),
        patch("src.cli.restore_db.download_backup_file") as mock_download,
    ):

        async def fake_download(key: str, dest: Path) -> None:
            async_dest = AsyncPath(dest)
            if key.endswith(".sha256"):
                await async_dest.write_text(f"{digest}  sample.dump\n", encoding="utf-8")
            else:
                await async_dest.write_bytes(data)

        mock_download.side_effect = fake_download

        is_valid, comp, exp = await verify_dump_checksum("logical_dumps/sample.dump")

        assert is_valid is True
        assert comp == digest
        assert exp == digest


@pytest.mark.asyncio
async def test_restore_logical_dump_pipeline(tmp_path: Path) -> None:
    data = b"PG_RESTORE_STREAM"
    digest = hashlib.sha256(data).hexdigest()

    mock_storage = MagicMock()
    mock_storage.list_backup_objects = AsyncMock(
        return_value=["logical_dumps/test_vault.dump", "logical_dumps/test_vault.dump.sha256"]
    )

    with (
        patch("src.cli.restore_db.ensure_temp_dir", return_value=tmp_path),
        patch("src.cli.restore_db.MinioObjectStorageService", return_value=mock_storage),
        patch("src.cli.restore_db.download_backup_file") as mock_dl,
        patch("asyncio.create_subprocess_exec") as mock_proc,
    ):

        async def fake_download(key: str, dest: Path) -> None:
            async_dest = AsyncPath(dest)
            if key.endswith(".sha256"):
                await async_dest.write_text(f"{digest}  test_vault.dump\n", encoding="utf-8")
            else:
                await async_dest.write_bytes(data)

        mock_dl.side_effect = fake_download

        mock_res = AsyncMock()
        mock_res.communicate.return_value = (b"", b"")
        mock_res.returncode = 0
        mock_proc.return_value = mock_res

        await restore_logical_dump(target_key="logical_dumps/test_vault.dump", jobs=4, clean=True)

        assert mock_proc.called
        cmd_args = mock_proc.call_args[0]
        assert cmd_args[0] == "pg_restore"
        assert "--jobs" in cmd_args
        assert "4" in cmd_args
        assert "--clean" in cmd_args


def test_generate_pitr_recovery_config(tmp_path: Path) -> None:
    pgdata = tmp_path / "pgdata"
    pgdata.mkdir()

    target_timestamp = "2026-08-14 18:00:00 UTC"
    generate_pitr_recovery_config(pgdata, target_time=target_timestamp)

    assert (pgdata / "recovery.signal").exists()
    auto_conf = (pgdata / "postgresql.auto.conf").read_text(encoding="utf-8")

    assert "restore_command = 'wal-g wal-fetch %f %p'" in auto_conf
    assert f"recovery_target_time = '{target_timestamp}'" in auto_conf
    assert "recovery_target_action = 'promote'" in auto_conf
