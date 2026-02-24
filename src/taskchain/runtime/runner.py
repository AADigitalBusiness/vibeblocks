import inspect
from typing import TypeVar, Union, Awaitable
from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome
from taskchain.core.executable import Executable

T = TypeVar("T")

class SyncRunner:
    """Executes workflows synchronously."""

    def run(self, executable: Executable[T], ctx: ExecutionContext[T]) -> Outcome[T]:
        """
        Runs the executable (Workflow, Process, or Task) synchronously.
        Raises RuntimeError if the executable returns an Awaitable (requires async execution).
        """
        result = executable.execute(ctx)

        if inspect.isawaitable(result):
            raise RuntimeError(
                "SyncRunner encountered an async executable (Coroutine). "
                "Use AsyncRunner for async workflows."
            )

        if isinstance(result, Outcome):
            return result

        raise RuntimeError(f"Executable returned unexpected type: {type(result)}")


class AsyncRunner:
    """Executes workflows asynchronously."""

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

        raise RuntimeError(f"Executable returned unexpected type: {type(result)}")
