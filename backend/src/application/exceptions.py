class ApplicationError(Exception):
    """Base architectural error boundary exception for all application tier violations."""


class UserAlreadyExistsError(ApplicationError):
    """Signaled when an execution sequence conflicts with a previously registered identity."""
