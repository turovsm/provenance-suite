class DomainError(Exception):
    """Base architectural error boundary exception for all domain tier violations."""


class InvalidEmailError(DomainError):
    """Signaled when an inbound string sequence violates RFC email constraints."""


class DomainInvariantError(DomainError):
    """Signaled when an action violates a fundamental business state constraint."""
