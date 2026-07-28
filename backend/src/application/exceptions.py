class ApplicationError(Exception):
    """Base architectural error boundary exception for all application tier violations."""


class UserAlreadyExistsError(ApplicationError):
    """Signaled when an execution sequence conflicts with a registered identity."""


class InvalidCredentialsError(ApplicationError):
    """Signaled when an inbound authentication verification fails."""


class UserDeactivatedError(ApplicationError):
    """Signaled when an action is attempted on a suspended user handle."""


class AlbumNotFoundError(ApplicationError):
    """Signaled when an operation targets a non-existent album aggregate root."""


class StorageUploadError(ApplicationError):
    """Signaled when object storage upload or processing fails."""
