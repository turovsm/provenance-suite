class ApplicationError(Exception):
    """Base architectural error boundary exception for all application tier violations."""


class UserAlreadyExistsError(ApplicationError):
    """Signaled when an execution sequence conflicts with a previously registered identity."""


class InvalidCredentialsError(ApplicationError):
    """Signaled when an inbound authentication verification signature pair fails validation."""


class UserDeactivatedError(ApplicationError):
    """Signaled when an execution block attempts actions on a suspended user handle."""
