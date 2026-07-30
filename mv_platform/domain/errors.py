class DomainError(Exception):
    """Base class for domain failures."""


class DomainValidationError(DomainError, ValueError):
    """Raised when a domain value violates its contract."""


class InvalidStateTransition(DomainError):
    """Raised when a runtime state transition is not allowed."""
