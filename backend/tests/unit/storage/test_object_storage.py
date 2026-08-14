import io

import pytest
from PIL import Image

from src.infrastructure.storage.object_storage import (
    InvalidImageFormatError,
    MinioObjectStorageService,
)


@pytest.fixture(scope="module")
def storage_service() -> MinioObjectStorageService:
    return MinioObjectStorageService()


def create_test_image_bytes(format: str = "JPEG", size: tuple[int, int] = (100, 100)) -> bytes:
    img = Image.new("RGBA", size, color=(255, 0, 0, 255))
    buf = io.BytesIO()
    if format.upper() == "JPEG":
        img = img.convert("RGB")
    img.save(buf, format=format)
    return buf.getvalue()


def test_verify_magic_bytes_valid(storage_service: MinioObjectStorageService) -> None:
    jpeg_bytes = create_test_image_bytes("JPEG")
    png_bytes = create_test_image_bytes("PNG")
    webp_bytes = create_test_image_bytes("WEBP")

    assert storage_service._verify_magic_bytes(jpeg_bytes) == "image/jpeg"
    assert storage_service._verify_magic_bytes(png_bytes) == "image/png"
    assert storage_service._verify_magic_bytes(webp_bytes) == "image/webp"


def test_verify_magic_bytes_invalid(storage_service: MinioObjectStorageService) -> None:
    with pytest.raises(InvalidImageFormatError, match="too small"):
        storage_service._verify_magic_bytes(b"short")

    with pytest.raises(InvalidImageFormatError, match="Unsupported image format"):
        storage_service._verify_magic_bytes(b"GIF89a" + b"\x00" * 20)


def test_normalize_cover_image_resizing_and_thumbhash(
    storage_service: MinioObjectStorageService,
) -> None:
    oversized_data = create_test_image_bytes("PNG", size=(1200, 800))
    normalized_jpeg, thumbhash_str = storage_service._normalize_cover_image(
        oversized_data, max_dim=500
    )

    assert isinstance(thumbhash_str, str)
    assert len(thumbhash_str) > 0

    img = Image.open(io.BytesIO(normalized_jpeg))
    assert img.format == "JPEG"
    assert max(img.size) <= 500


def test_get_public_url() -> None:
    url = MinioObjectStorageService.get_public_url("covers/album1/front.jpg")
    assert url.endswith("/provenance-covers/covers/album1/front.jpg")
