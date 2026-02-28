from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union, Awaitable
from vibeflow.core.context import ExecutionContext
from vibeflow.core.outcome import Outcome

T = TypeVar("T")


class Executable(Generic[T], ABC):
    """Abstract base class for all executable units in VibeFlow."""

    @property
    @abstractmethod
    def is_async(self) -> bool:
        """
        Determines if this executable requires asynchronous execution.
        """
        ...

    @abstractmethod
    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        """
        Executes the unit of work.

        Returns:
            Outcome[T] if synchronous.
            Awaitable[Outcome[T]] if asynchronous.
        """
        ...

    @abstractmethod
    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        """
        Rolls back the changes made by this unit.

        Returns:
            None if synchronous.
            Awaitable[None] if asynchronous.
        """
        ...
