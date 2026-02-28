import inspect
from typing import TypeVar

from vibeflow.core.context import ExecutionContext
from vibeflow.core.executable import Executable
from vibeflow.core.outcome import Outcome

T = TypeVar("T")


class SyncRunner:
    """Executes flows synchronously."""

    def run(self, executable: Executable[T], ctx: ExecutionContext[T]) -> Outcome[T]:
        """
        Runs the executable (Flow, Chain, or Beat) synchronously.
        Raises RuntimeError if the executable returns an Awaitable (requires async execution).
        """
        result = executable.execute(ctx)

        if inspect.isawaitable(result):
            raise RuntimeError(
                "SyncRunner encountered an async executable (Coroutine). "
                "Use AsyncRunner for async flows."
            )

        if isinstance(result, Outcome):
            return result

        raise RuntimeError(
            f"Executable returned unexpected type: {type(result)}")


class AsyncRunner:
    """Executes flows asynchronously."""

    async def run(self, executable: Executable[T], ctx: ExecutionContext[T]) -> Outcome[T]:
        """
        Runs the executable asynchronously.
        Handles both sync (Outcome) and async (Awaitable[Outcome]) returns.
        """
        result = executable.execute(ctx)

        if inspect.isawaitable(result):
            return await result

        if isinstance(result, Outcome):
            return result

        raise RuntimeError(
            f"Executable returned unexpected type: {type(result)}")
