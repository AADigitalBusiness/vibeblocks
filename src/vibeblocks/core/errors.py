class VibeBlocksError(Exception):
    """Base exception for all VibeBlocks errors."""
    pass


class BlockExecutionError(VibeBlocksError):
    """Raised when a Block fails to execute."""
    pass


class BlockTimeoutError(BlockExecutionError):
    """Raised when a Block exceeds its allocated execution time."""
    pass


class ChainExecutionError(VibeBlocksError):
    """Raised when a Chain fails (bubbling up from a Block)."""
    pass
