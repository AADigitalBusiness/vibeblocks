"""
Process component handling linear execution of multiple tasks.
"""

import inspect
from typing import List, Union, Awaitable, TypeVar

from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome
from taskchain.core.executable import Executable
from taskchain.core.errors import ProcessExecutionError
from taskchain.components.task import Task

T = TypeVar("T")

class Process(Executable[T]):
    """
    A linear collection of executables (Tasks or sub-Processes).
    Executes steps sequentially.
    """
    def __init__(self, name: str, steps: List[Executable[T]]):
        self.name = name
        self.steps = steps

    @property
    def is_async(self) -> bool:
        """Recursively checks if any step requires async execution."""
        return any(step.is_async for step in self.steps)

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
             return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Process Started")
        for step in self.steps:
            try:
                result = step.execute(ctx)

                # Safety check for unexpected async returns in sync mode
                if inspect.isawaitable(result):
                    raise ProcessExecutionError(f"Step '{getattr(step, 'name', 'Unknown')}' returned a coroutine in a sync process execution. Use AsyncRunner.")

                # Check outcome
                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                         # Stop execution and bubble up failure
                         return result
            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Process Error: {str(e)}")
                # Wrap unknown errors in ProcessExecutionError
                raise ProcessExecutionError(f"Process '{self.name}' failed") from e

        ctx.log_event("INFO", self.name, "Process Completed")
        ctx.completed_steps.add(self.name)
        return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=0)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Process Started (Async)")
        for step in self.steps:
            try:
                result = step.execute(ctx)
                if inspect.isawaitable(result):
                    result = await result

                if isinstance(result, Outcome):
                     if result.status != "SUCCESS":
                         return result
            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Process Error: {str(e)}")
                raise ProcessExecutionError(f"Process '{self.name}' failed") from e

        ctx.log_event("INFO", self.name, "Process Completed")
        ctx.completed_steps.add(self.name)
        return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=0)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.is_async:
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Process")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                if inspect.isawaitable(res):
                    raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned an async compensation in a sync process. Use AsyncRunner.")
        return None

    async def _compensate_async(self, ctx: ExecutionContext[T]) -> None:
        ctx.log_event("INFO", self.name, "Compensating Process (Async)")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                if inspect.isawaitable(res):
                    await res

    def _did_step_succeed(self, ctx: ExecutionContext[T], step: Executable[T]) -> bool:
        """Checks trace to see if the step completed successfully."""
        name = getattr(step, "name", None)
        if not name:
            return False

        return name in ctx.completed_steps
