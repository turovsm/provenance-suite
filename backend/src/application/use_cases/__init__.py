from src.application.use_cases.authenticate_user import (
    AuthenticateUserRequest,
    AuthenticateUserResponse,
    AuthenticateUserUseCase,
)
from src.application.use_cases.delete_album import (
    AlbumNotFoundError,
    DeleteAlbumRequest,
    DeleteAlbumUseCase,
)
from src.application.use_cases.ingest_album import (
    ArchiveIngestDTO,
    ArchiveLinkIngestDTO,
    CoverIngestDTO,
    DiscIngestDTO,
    ExternalLinkIngestDTO,
    IngestAlbumRequest,
    IngestAlbumResponse,
    IngestAlbumUseCase,
    TrackIngestDTO,
)
from src.application.use_cases.list_albums import (
    GetAlbumDetailRequest,
    GetAlbumDetailUseCase,
    ListAlbumsRequest,
    ListAlbumsResponse,
    ListAlbumsUseCase,
)
from src.application.use_cases.register_user import (
    RegisterUserRequest,
    RegisterUserResponse,
    RegisterUserUseCase,
)


__all__ = [
    "RegisterUserUseCase",
    "RegisterUserRequest",
    "RegisterUserResponse",
    "AuthenticateUserUseCase",
    "AuthenticateUserRequest",
    "AuthenticateUserResponse",
    "IngestAlbumUseCase",
    "IngestAlbumRequest",
    "IngestAlbumResponse",
    "TrackIngestDTO",
    "DiscIngestDTO",
    "ArchiveLinkIngestDTO",
    "ArchiveIngestDTO",
    "ExternalLinkIngestDTO",
    "CoverIngestDTO",
    "ListAlbumsUseCase",
    "ListAlbumsRequest",
    "ListAlbumsResponse",
    "GetAlbumDetailUseCase",
    "GetAlbumDetailRequest",
    "DeleteAlbumUseCase",
    "DeleteAlbumRequest",
    "AlbumNotFoundError",
]
