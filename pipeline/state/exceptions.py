class StateError(Exception):
    """Base class for state exceptions."""
    pass

class InvalidStateTransition(StateError):
    """Raised when an invalid state transition is attempted."""
    pass

class ConcurrentUpdateError(StateError):
    """Raised when a concurrent update prevents state transition."""
    pass

class EntityNotFoundError(StateError):
    """Raised when the entity to transition is not found."""
    pass

class IdempotencyError(StateError):
    """Base class for idempotency errors."""
    pass

class DuplicateProcessingError(IdempotencyError):
    """Raised when duplicate processing is attempted."""
    pass
