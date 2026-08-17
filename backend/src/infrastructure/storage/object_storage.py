import base64
import io
import json
import logging
from pathlib import Path
from typing import Any

import anyio
import thumbhash
from minio import Minio
from minio.error import S3Error
from PIL import Image

from src.config import settings


logger = logging.getLogger("provenance.storage")


class InvalidImageFormatError(Exception):
    """Raised when uploaded file fails magic byte inspection."""


class MinioObjectStorageService:
    def __init__(self) -> None:
        self._client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._bucket = settings.MINIO_BUCKET_NAME

    def ensure_bucket_and_policy(self) -> None:
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info("Created MinIO bucket '%s'", self._bucket)

            public_read_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
                    }
                ],
            }
            self._client.set_bucket_policy(self._bucket, json.dumps(public_read_policy))
            logger.info("Successfully set public read policy on bucket '%s'", self._bucket)
        except Exception as exc:
            logger.warning("Failed to configure policy on bucket '%s': %s", self._bucket, exc)

    @staticmethod
    def _verify_magic_bytes(data: bytes) -> str:
        if len(data) < 12:
            raise InvalidImageFormatError("File buffer payload is too small.")

        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            return "image/webp"

        raise InvalidImageFormatError("Unsupported image format. Allowed formats: JPEG, PNG, WEBP.")

    @staticmethod
    def _generate_thumbhash(img_rgba: Image.Image) -> str:
        img_thumb = img_rgba.copy()
        img_thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
        tw, th = img_thumb.size
        hash_bytes = thumbhash.rgba_to_thumb_hash(tw, th, img_thumb.tobytes())
        return base64.b64encode(bytes(hash_bytes)).decode("ascii")

    @staticmethod
    def _resize_and_compress_jpeg(img: Image.Image, target_dim: int) -> bytes:
        img_rgb = img.convert("RGB")
        width, height = img_rgb.size
        if width > target_dim or height > target_dim:
            img_rgb.thumbnail((target_dim, target_dim), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img_rgb.save(
            buffer,
            format="JPEG",
            quality=settings.IMAGE_JPEG_QUALITY,
            optimize=True,
        )
        return buffer.getvalue()

    def _normalize_cover_image(self, data: bytes, max_dim: int | None = None) -> tuple[bytes, str]:
        self._verify_magic_bytes(data)
        target_dim = max_dim or settings.COVER_IMAGE_MAX_DIMENSION

        with Image.open(io.BytesIO(data)) as img:
            img_rgba = img.convert("RGBA")
            thumb_hash_str = self._generate_thumbhash(img_rgba)
            processed_bytes = self._resize_and_compress_jpeg(img, target_dim)

        return processed_bytes, thumb_hash_str

    def _normalize_entity_image(self, data: bytes, max_dim: int | None = None) -> bytes:
        self._verify_magic_bytes(data)
        target_dim = max_dim or settings.ENTITY_IMAGE_MAX_DIMENSION

        with Image.open(io.BytesIO(data)) as img:
            return self._resize_and_compress_jpeg(img, target_dim)

    async def upload_cover(self, object_key: str, data: bytes) -> tuple[str, str]:
        def _upload() -> tuple[str, str]:
            self.ensure_bucket_and_policy()
            processed_data, thumb_hash_str = self._normalize_cover_image(data)
            data_stream = io.BytesIO(processed_data)

            self._client.put_object(
                bucket_name=self._bucket,
                object_name=object_key,
                data=data_stream,
                length=len(processed_data),
                content_type="image/jpeg",
            )
            return object_key, thumb_hash_str

        return await anyio.to_thread.run_sync(_upload)

    async def upload_entity_avatar(self, entity_type: str, entity_id: Any, data: bytes) -> str:
        def _upload() -> str:
            self.ensure_bucket_and_policy()
            processed_data = self._normalize_entity_image(data)
            object_key = f"entities/{entity_type}/{entity_id}.jpg"
            data_stream = io.BytesIO(processed_data)

            self._client.put_object(
                bucket_name=self._bucket,
                object_name=object_key,
                data=data_stream,
                length=len(processed_data),
                content_type="image/jpeg",
            )
            return object_key

        return await anyio.to_thread.run_sync(_upload)

    async def upload_backup_file(
        self, object_key: str, file_path: str, content_type: str = "application/octet-stream"
    ) -> str:
        def _upload() -> str:
            self.ensure_backup_bucket()
            self._client.fput_object(
                bucket_name=settings.BACKUP_BUCKET_NAME,
                object_name=object_key,
                file_path=file_path,
                content_type=content_type,
            )
            return object_key

        return await anyio.to_thread.run_sync(_upload)

    async def list_backup_objects(self, prefix: str) -> list[str]:
        def _list() -> list[str]:
            self.ensure_backup_bucket()
            objects = self._client.list_objects(
                bucket_name=settings.BACKUP_BUCKET_NAME, prefix=prefix, recursive=True
            )
            return [obj.object_name for obj in objects if obj.object_name]

        return await anyio.to_thread.run_sync(_list)

    @staticmethod
    def get_public_url(object_key: str) -> str:
        base = settings.MINIO_PUBLIC_BASE_URL.rstrip("/")
        key = object_key.lstrip("/")
        return f"{base}/{key}"

    def ensure_backup_bucket(self) -> None:
        bucket = settings.BACKUP_BUCKET_NAME
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
            logger.info("Created private MinIO backup bucket '%s'", bucket)

    async def upload_backup(self, object_key: str, data: bytes) -> str:
        def _upload() -> str:
            self.ensure_backup_bucket()
            self._client.put_object(
                bucket_name=settings.BACKUP_BUCKET_NAME,
                object_name=object_key,
                data=io.BytesIO(data),
                length=len(data),
                content_type="application/octet-stream",
            )
            return object_key

        return await anyio.to_thread.run_sync(_upload)

    async def download_backup_file(self, object_key: str, file_path: str | Path) -> None:
        def _download() -> None:
            self.ensure_backup_bucket()
            self._client.fget_object(
                bucket_name=settings.BACKUP_BUCKET_NAME,
                object_name=object_key,
                file_path=str(file_path),
            )

        await anyio.to_thread.run_sync(_download)

    async def prune_backups(self, prefix: str, keep: int) -> list[str]:
        def _prune() -> list[str]:
            bucket = settings.BACKUP_BUCKET_NAME
            objects = self._client.list_objects(bucket, prefix=prefix, recursive=True)
            names = sorted((obj.object_name for obj in objects), reverse=True)
            stale = names[keep:]
            for name in stale:
                try:
                    self._client.remove_object(bucket, name)
                except S3Error as exc:
                    logger.warning("Failed to prune backup object '%s': %s", name, exc)
            return stale

        return await anyio.to_thread.run_sync(_prune)

    async def delete_cover(self, object_key: str) -> None:
        def _delete() -> None:
            try:
                self._client.remove_object(self._bucket, object_key)
            except S3Error:
                pass

        await anyio.to_thread.run_sync(_delete)
