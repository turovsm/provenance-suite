from src.presentation.schemas.auth import TokenResponseSchema, UserLoginRequestSchema
from src.presentation.schemas.music import (
    AlbumIngestRequestSchema,
    AlbumIngestResponseSchema,
    ArchiveIngestSchema,
    ArchiveLinkIngestSchema,
    CoverIngestSchema,
    DiscIngestSchema,
    ExternalLinkIngestSchema,
    TrackIngestSchema,
)
from src.presentation.schemas.user import UserRegisterRequestSchema, UserResponseSchema


__all__ = [
    "UserRegisterRequestSchema",
    "UserResponseSchema",
    "UserLoginRequestSchema",
    "TokenResponseSchema",
    "TrackIngestSchema",
    "DiscIngestSchema",
    "ArchiveLinkIngestSchema",
    "ArchiveIngestSchema",
    "ExternalLinkIngestSchema",
    "CoverIngestSchema",
    "AlbumIngestRequestSchema",
    "AlbumIngestResponseSchema",
]
