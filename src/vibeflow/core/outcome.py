from dataclasses import dataclass, field
from typing import Generic, TypeVar, Literal, List
from vibeflow.core.context import ExecutionContext

T = TypeVar("T")


@dataclass
class Outcome(Generic[T]):
    """Represents the final result of a workflow or task execution."""
    status: Literal["SUCCESS", "FAILED", "ABORTED"]
    context: ExecutionContext[T]
    errors: List[Exception] = field(default_factory=list)
    duration_ms: int = 0
