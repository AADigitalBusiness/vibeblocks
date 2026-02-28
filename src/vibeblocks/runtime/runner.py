import inspect
from typing import TypeVar

from vibeblocks.core.context import ExecutionContext
from vibeblocks.core.executable import Executable
from vibeblocks.core.outcome import Outcome

T = TypeVar("T")


class SyncRunner:
    """Executes flows synchronously."""

    def run(self, executable: Executable[T], ctx: ExecutionContext[T]) -> Outcome[T]:
        """
        Runs the executable (Flow, Chain, or Block) synchronously.
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
