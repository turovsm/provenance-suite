import io

import anyio
from minio import Minio
from minio.error import S3Error

from src.config import settings


class MinioObjectStorageService:
    def __init__(self) -> None:
        self._client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self._bucket = settings.MINIO_BUCKET_NAME

    def _ensure_bucket_exists(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def upload_cover(
        self, object_key: str, data: bytes, mime_type: str = "image/jpeg"
    ) -> str:
        def _upload() -> str:
            self._ensure_bucket_exists()
            data_stream = io.BytesIO(data)
            self._client.put_object(
                bucket_name=self._bucket,
                object_name=object_key,
                data=data_stream,
                length=len(data),
                content_type=mime_type,
            )
            return object_key

        return await anyio.to_thread.run_sync(_upload)

    async def get_cover(self, object_key: str) -> tuple[bytes, str]:
        def _fetch() -> tuple[bytes, str]:
            response = self._client.get_object(self._bucket, object_key)
            try:
                content_type = response.headers.get("content-type", "image/jpeg")
                data = response.read()
                return data, content_type
            finally:
                response.close()
                response.release_conn()

        return await anyio.to_thread.run_sync(_fetch)

    async def delete_cover(self, object_key: str) -> None:
        def _delete() -> None:
            try:
                self._client.remove_object(self._bucket, object_key)
            except S3Error:
                pass

        await anyio.to_thread.run_sync(_delete)
