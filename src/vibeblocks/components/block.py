import asyncio
import concurrent.futures
import inspect
import time
from typing import Any, Awaitable, Callable, Optional, TypeVar, Union

from vibeblocks.core.context import ExecutionContext
from vibeblocks.core.errors import BlockExecutionError, BlockTimeoutError
from vibeblocks.core.executable import Executable
from vibeblocks.core.outcome import Outcome
from vibeblocks.policies.retry import RetryPolicy
from vibeblocks.utils.inspection import is_async_callable

T = TypeVar("T")

# Shared executor for synchronous block timeouts to avoid overhead and thread leakage.
# Using a large enough number of workers to handle concurrent blocks.
_TASK_TIMEOUT_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    thread_name_prefix="BlockTimeout")


class Block(Executable[T]):
    """
    Represents an atomic unit of work in a workflow.
    Executes a function with retry logic and supports compensation.
    """

    def __init__(
        self,
        name: str,
        func: Callable[[ExecutionContext[T]], Any],
        description: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
        undo: Optional[Callable[[ExecutionContext[T]], Any]] = None,
        timeout: Optional[float] = None,
    ):
        self.name = name
        self.func = func
        self.description = description or func.__doc__
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=1)
        self.undo = undo
        self.timeout = timeout

        self._is_async = is_async_callable(self.func)
        self._is_undo_async = is_async_callable(
            self.undo) if self.undo else False

    @property
    def is_async(self) -> bool:
        """Determines if the block function is asynchronous."""
        # Optimized: Return pre-calculated value to avoid repeated inspection overhead
        return self._is_async

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
            return self._execute_async(ctx)
        else:
            return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Block Started")
        start_time = time.time()
        attempt = 1

        while True:
            try:
                if self.timeout:
                    try:
                        future = _TASK_TIMEOUT_EXECUTOR.submit(self.func, ctx)
                        res = future.result(timeout=self.timeout)
                    except concurrent.futures.TimeoutError:
                        raise BlockTimeoutError(
                            f"Block '{self.name}' timed out after {self.timeout}s"
                        ) from None
                else:
                    res = self.func(ctx)

                # Runtime check for false-negative async detection (e.g. lambdas)
                if inspect.isawaitable(res):
                    if inspect.iscoroutine(res):
                        res.close()
                    # We cannot await it here because we are in sync mode.
                    # We must warn the user that their block logic probably didn't run.
                    # Or raise an error? Raising error is safer.
                    msg = (
                        f"Block '{self.name}' returned an awaitable (coroutine) but "
                        "was executed synchronously. Check if the function is "
                        "defined correctly or if AsyncRunner should be used."
                    )
                    raise RuntimeError(msg)

                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("INFO", self.name, "Block Completed")
                ctx.completed_steps.add(self.name)
                return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

            except Exception as e:
                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("ERROR", self.name,
                              f"Block Failed: {ctx.format_exception(e)}")

                if self.retry_policy.should_retry(attempt, e):
                    delay = self.retry_policy.calculate_delay(attempt)
                    msg = (
                        f"Retrying in {delay}s (Attempt {attempt}/"
                        f"{self.retry_policy.max_attempts})"
                    )
                    ctx.log_event("INFO", self.name, msg)
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    msg = f"Block '{self.name}' failed after {attempt} attempts"
                    error = BlockExecutionError(msg)
                    error.__cause__ = e
                    return Outcome(
                        status="FAILED", context=ctx, errors=[error], duration_ms=duration
                    )

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Block Started (Async)")
        start_time = time.time()
        attempt = 1

        while True:
            try:
                res = self.func(ctx)
                if inspect.isawaitable(res):
                    if self.timeout:
                        try:
                            res = await asyncio.wait_for(res, timeout=self.timeout)
                        except asyncio.TimeoutError:
                            raise BlockTimeoutError(
                                f"Block '{self.name}' timed out after {self.timeout}s"
                            ) from None
                    else:
                        res = await res

                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("INFO", self.name, "Block Completed")
                ctx.completed_steps.add(self.name)
                return Outcome(status="SUCCESS", context=ctx, errors=[], duration_ms=duration)

            except Exception as e:
                duration = int((time.time() - start_time) * 1000)
                ctx.log_event("ERROR", self.name,
                              f"Block Failed: {ctx.format_exception(e)}")

                if self.retry_policy.should_retry(attempt, e):
                    delay = self.retry_policy.calculate_delay(attempt)
                    msg = (
                        f"Retrying in {delay}s (Attempt {attempt}/"
                        f"{self.retry_policy.max_attempts})"
                    )
                    ctx.log_event("INFO", self.name, msg)
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                else:
                    msg = f"Block '{self.name}' failed after {attempt} attempts"
                    error = BlockExecutionError(msg)
                    error.__cause__ = e
                    return Outcome(
                        status="FAILED", context=ctx, errors=[error], duration_ms=duration
                    )

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.undo is None:
            return None

        ctx.log_event("INFO", self.name, "Compensating Block")

        if self._is_undo_async:
            return self._compensate_async(ctx)
        else:
            try:
                self.undo(ctx)
            except Exception as e:
                ctx.log_event("ERROR", self.name,
                              f"Compensation Failed: {ctx.format_exception(e)}")
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
            ctx.log_event("ERROR", self.name,
                          f"Compensation Failed: {ctx.format_exception(e)}")
            raise
