class TaskChainError(Exception):
    """Base exception for all TaskChain errors."""
    pass

class TaskExecutionError(TaskChainError):
    """Raised when a Task fails to execute."""
    pass

class ProcessExecutionError(TaskChainError):
    """Raised when a Process fails (bubbling up from a Task)."""
    pass

class WorkflowExecutionError(TaskChainError):
    """Raised when a Workflow fails to orchestrate."""
    pass

class CompensationError(TaskChainError):
    """Raised when compensation logic fails."""
    pass
