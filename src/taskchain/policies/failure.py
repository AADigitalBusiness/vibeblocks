from enum import Enum, auto

class FailureStrategy(Enum):
    """
    Defines the behavior when a workflow or process encounters an error.
    """
    ABORT = auto()
    """Stop execution immediately. No compensation."""

    CONTINUE = auto()
    """Log the error and proceed to the next step. Context may be partial."""

    COMPENSATE = auto()
    """Stop execution and run compensation logic (undo) on successful steps in reverse order."""
