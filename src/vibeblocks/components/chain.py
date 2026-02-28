"""
Chain component handling linear execution of multiple blocks.
"""

import inspect
import time
from typing import List, Union, Awaitable, TypeVar

from vibeblocks.core.context import ExecutionContext
from vibeblocks.core.outcome import Outcome
from vibeblocks.core.executable import Executable
from vibeblocks.core.errors import ChainExecutionError

T = TypeVar("T")


class Chain(Executable[T]):
    """
    A linear collection of executables (blocks or sub-chains).
    Executes steps sequentially.
    """

    def __init__(self, name: str, steps: List[Executable[T]]):
        self.name = name
        self.steps = list(steps)
        self._is_async = any(step.is_async for step in self.steps)

    @property
    def is_async(self) -> bool:
        """Determines if the chain requires asynchronous execution."""
        return self._is_async

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
            return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Chain Started")

        for step in self.steps:
            try:
                result = step.execute(ctx)

                # Safety check for unexpected async returns in sync mode
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    raise ChainExecutionError(
                        f"Step '{getattr(step, 'name', 'Unknown')}' returned a coroutine in a sync chain execution. Use AsyncRunner.")

                # Check outcome
                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                        # Stop execution and bubble up failure
                        return result
            except Exception as e:
                duration = (time.perf_counter_ns() - start_time) // 1_000_000
                ctx.log_event("ERROR", self.name,
                              f"Chain Error: {ctx.format_exception(e)}")
                # Return Failed Outcome instead of raising
                return Outcome(status="FAILED", context=ctx, errors=[e], duration_ms=duration)

        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        ctx.log_event("INFO", self.name, "Chain Completed")
        ctx.completed_steps.add(self.name)
        return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Chain Started (Async)")

        for step in self.steps:
            try:
                result = step.execute(ctx)
                if inspect.isawaitable(result):
                    result = await result

                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                        return result
            except Exception as e:
                duration = (time.perf_counter_ns() - start_time) // 1_000_000
                ctx.log_event("ERROR", self.name,
                              f"Chain Error: {ctx.format_exception(e)}")
                # Return Failed Outcome instead of raising
                return Outcome(status="FAILED", context=ctx, errors=[e], duration_ms=duration)

        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        ctx.log_event("INFO", self.name, "Chain Completed")
        ctx.completed_steps.add(self.name)
        return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.is_async:
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Chain")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                if inspect.isawaitable(res):
                    if inspect.iscoroutine(res):
                        res.close()
                    raise RuntimeError(
                        f"Step '{getattr(step, 'name', 'Unknown')}' returned an async compensation in a sync chain. Use AsyncRunner.")
        return None

    async def _compensate_async(self, ctx: ExecutionContext[T]) -> None:
        ctx.log_event("INFO", self.name, "Compensating Chain (Async)")
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
