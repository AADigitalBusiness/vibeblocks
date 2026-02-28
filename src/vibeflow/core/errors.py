class VibeFlowError(Exception):
    """Base exception for all VibeFlow errors."""
    pass

class BeatExecutionError(VibeFlowError):
    """Raised when a Beat fails to execute."""
    pass


class BeatTimeoutError(BeatExecutionError):
    """Raised when a Beat exceeds its allocated execution time."""
    pass

class ChainExecutionError(VibeFlowError):
    """Raised when a Chain fails (bubbling up from a Beat)."""
    pass
