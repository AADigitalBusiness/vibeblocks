import inspect
import time
import asyncio
from typing import Callable, Optional, Awaitable, Union, Any, TypeVar, Generic, cast
import warnings

from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome
from taskchain.core.executable import Executable
from taskchain.core.errors import TaskExecutionError
from taskchain.policies.retry import RetryPolicy
from taskchain.utils.inspection import is_async_callable

T = TypeVar("T")

class Task(Executable[T]):
    """
    Represents an atomic unit of work in a workflow.
    Executes a function with retry logic and supports compensation.
    """

    def __init__(
        self,
        name: str,
        func: Callable[[ExecutionContext[T]], Any],
        retry_policy: Optional[RetryPolicy] = None,
        undo: Optional[Callable[[ExecutionContext[T]], Any]] = None,
    ):
        self.name = name
        self.func = func
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        self.undo = undo

    @property
    def is_async(self) -> bool:
        """Determines if the task function is asynchronous."""
        return is_async_callable(self.func)

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
            return self._execute_async(ctx)
        else:
            return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Task Started")
        start_time = time.time()
        attempt = 1

        while True:
            try:
                res = self.func(ctx)

                # Runtime check for false-negative async detection (e.g. lambdas returning coroutines)
                if inspect.isawaitable(res):
                    # We cannot await it here because we are in sync mode.
                    # We must warn the user that their task logic probably didn't run.
                    # Or raise an error? Raising error is safer.
                    raise RuntimeError(f"Task '{self.name}' returned an awaitable (coroutine) but was executed synchronously. Check if the function is defined correctly or if AsyncRunner should be used.")

                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("INFO", self.name, "Task Completed")
                return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

            except Exception as e:
                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("ERROR", self.name, f"Task Failed: {str(e)}")

                if self.retry_policy.should_retry(attempt, e):
                    delay = self.retry_policy.calculate_delay(attempt)
                    ctx.log_event("INFO", self.name, f"Retrying in {delay}s (Attempt {attempt}/{self.retry_policy.max_attempts})")
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    error = TaskExecutionError(f"Task '{self.name}' failed after {attempt} attempts")
                    error.__cause__ = e
                    return Outcome(status="FAILED", context=ctx, errors=[error], duration_ms=duration)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Task Started (Async)")
        start_time = time.time()
        attempt = 1

        while True:
            try:
                res = self.func(ctx)
                if inspect.isawaitable(res):
                    await res

                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("INFO", self.name, "Task Completed")
                return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

            except Exception as e:
                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("ERROR", self.name, f"Task Failed: {str(e)}")

                if self.retry_policy.should_retry(attempt, e):
                    delay = self.retry_policy.calculate_delay(attempt)
                    ctx.log_event("INFO", self.name, f"Retrying in {delay}s (Attempt {attempt}/{self.retry_policy.max_attempts})")
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    error = TaskExecutionError(f"Task '{self.name}' failed after {attempt} attempts")
                    error.__cause__ = e
                    return Outcome(status="FAILED", context=ctx, errors=[error], duration_ms=duration)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.undo is None:
            return None

        ctx.log_event("INFO", self.name, "Compensating Task")

        undo_fn = self.undo
        is_undo_async = is_async_callable(undo_fn)

        if is_undo_async:
            return self._compensate_async(ctx)
        else:
            try:
                undo_fn(ctx)
            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Compensation Failed: {str(e)}")
                raise
            return None

    async def _compensate_async(self, ctx: ExecutionContext[T]) -> None:
        if self.undo is None:
            return

        try:
            res = self.undo(ctx)
            if inspect.isawaitable(res):
                await res
        except Exception as e:
            ctx.log_event("ERROR", self.name, f"Compensation Failed: {str(e)}")
            raise
