"""
Workflow orchestrator for executing trees of Tasks and Processes.
Handles high-level failure policies.
"""

import inspect
import time
from typing import Awaitable, List, Literal, Optional, Tuple, TypeVar, Union

from taskchain.core.context import ExecutionContext
from taskchain.core.executable import Executable
from taskchain.core.outcome import Outcome
from taskchain.policies.failure import FailureStrategy

T = TypeVar("T")


class Workflow(Executable[T]):
    """
    The top-level orchestrator that manages a sequence of steps (Tasks or Processes)
    and handles failures according to a strategy.
    """
    def __init__(
        self,
        name: str,
        steps: List[Executable[T]],
        strategy: FailureStrategy = FailureStrategy.ABORT
    ):
        self.name = name
        self.steps = list(steps)
        self.strategy = strategy
        self._is_async = any(step.is_async for step in self.steps)

    @property
    def is_async(self) -> bool:
        """Recursively checks if any step requires async execution."""
        return self._is_async

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
            return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Workflow Started")
        collected_errors = []

        for step in self.steps:
            step_errors = []
            try:
                result = step.execute(ctx)

                self._ensure_not_awaitable(
                    result, getattr(step, "name", "Unknown"), "step execution"
                )

                if isinstance(result, Outcome) and result.status != "SUCCESS":
                    action, outcome = self._handle_failure_strategy(
                        ctx, step, result.errors, start_time
                    )
                    if action == "ABORT":
                        return outcome
                    elif action == "CONTINUE":
                        collected_errors.extend(result.errors)
                        continue
                    elif action == "COMPENSATE":
                        res = step.compensate(ctx)
                        self._ensure_not_awaitable(
                            res, getattr(step, "name", "Unknown"), "step compensation"
                        )
                        self.compensate(ctx)
                        if outcome:
                            outcome.duration_ms = (
                                time.perf_counter_ns() - start_time
                            ) // 1_000_000
                        return outcome

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                step_errors = [e]

            if step_errors:
                outcome = self._handle_sync_step_failure(ctx, step, step_errors, start_time)
                if outcome:
                    return outcome
                collected_errors.extend(step_errors)

        return self._finish_workflow(ctx, collected_errors, start_time)

    def _handle_sync_step_failure(
        self,
        ctx: ExecutionContext[T],
        step: Executable[T],
        errors: List[Exception],
        start_time: int,
    ) -> Union[Outcome[T], None]:
        """
        Handles failure logic for a synchronous step based on the workflow's strategy.
        Returns an Outcome if the workflow should stop, or None if it should continue.
        """
        step_name = getattr(step, "name", "Unknown")
        duration = (time.perf_counter_ns() - start_time) // 1_000_000

        if self.strategy == FailureStrategy.ABORT:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Aborted due to failure in step '{step_name}'",
            )
            return Outcome("ABORTED", ctx, errors, duration_ms=duration)

        elif self.strategy == FailureStrategy.CONTINUE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Continuing after failure in step '{step_name}'",
            )
            return None

        elif self.strategy == FailureStrategy.COMPENSATE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Compensating due to failure in step '{step_name}'",
            )

            # Compensate the current failing step
            res = step.compensate(ctx)
            if inspect.isawaitable(res):
                if inspect.iscoroutine(res):
                    res.close()
                raise RuntimeError(
                    f"Step '{step_name}' returned an async compensation "
                    "in a sync workflow. Use AsyncRunner."
                )

            # Compensate previous steps
            self.compensate(ctx)
            return Outcome("FAILED", ctx, errors, duration_ms=duration)

        return None
    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Workflow Started (Async)")
        collected_errors = []

        for step in self.steps:
            try:
                result = step.execute(ctx)
                if inspect.isawaitable(result):
                    result = await result

                if isinstance(result, Outcome) and result.status != "SUCCESS":
                    action, outcome = self._handle_failure_strategy(
                        ctx, step, result.errors, start_time
                    )
                    if action == "ABORT":
                        return outcome
                    elif action == "CONTINUE":
                        collected_errors.extend(result.errors)
                        continue
                    elif action == "COMPENSATE":
                        res = step.compensate(ctx)
                        if inspect.isawaitable(res):
                            await res

                        res = self.compensate(ctx)
                        if inspect.isawaitable(res):
                            await res
                        if outcome:
                            outcome.duration_ms = (
                                time.perf_counter_ns() - start_time
                            ) // 1_000_000
                        return outcome

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                collected_errors.append(e)

                action, outcome = self._handle_failure_strategy(
                    ctx, step, [e], start_time
                )
                if action == "ABORT":
                    return outcome
                elif action == "CONTINUE":
                    continue
                elif action == "COMPENSATE":
                    res = step.compensate(ctx)
                    if inspect.isawaitable(res):
                        await res

                    res = self.compensate(ctx)
                    if inspect.isawaitable(res):
                        await res
                    if outcome:
                        outcome.duration_ms = (
                            time.perf_counter_ns() - start_time
                        ) // 1_000_000
                    return outcome

        return self._finish_workflow(ctx, collected_errors, start_time)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.is_async:
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Workflow")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                self._ensure_not_awaitable(
                    res, getattr(step, "name", "Unknown"), "compensation"
                )
        return None

    async def _compensate_async(self, ctx: ExecutionContext[T]) -> None:
        ctx.log_event("INFO", self.name, "Compensating Workflow (Async)")
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

    def _ensure_not_awaitable(self, result, step_name: str, context: str) -> None:
        if inspect.isawaitable(result):
            if inspect.iscoroutine(result):
                result.close()
            raise RuntimeError(
                f"Step '{step_name}' returned a coroutine "
                f"in a sync workflow ({context}). Use AsyncRunner."
            )

    def _handle_failure_strategy(
        self,
        ctx: ExecutionContext[T],
        step: Executable[T],
        errors: List[Exception],
        start_time: int,
    ) -> Tuple[Literal["ABORT", "CONTINUE", "COMPENSATE"], Optional[Outcome[T]]]:
        if self.strategy == FailureStrategy.ABORT:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Aborted due to failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            duration = (time.perf_counter_ns() - start_time) // 1_000_000
            return "ABORT", Outcome("ABORTED", ctx, errors, duration_ms=duration)

        elif self.strategy == FailureStrategy.CONTINUE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Continuing after failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            return "CONTINUE", None

        elif self.strategy == FailureStrategy.COMPENSATE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Workflow Compensating due to failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            duration = (time.perf_counter_ns() - start_time) // 1_000_000
            return "COMPENSATE", Outcome("FAILED", ctx, errors, duration_ms=duration)

        return "CONTINUE", None

    def _finish_workflow(
        self, ctx: ExecutionContext[T], collected_errors: List[Exception], start_time: int
    ) -> Outcome[T]:
        final_status: Literal["SUCCESS", "FAILED"] = (
            "FAILED" if collected_errors else "SUCCESS"
        )
        ctx.log_event("INFO", self.name, f"Workflow Completed with status {final_status}")

        if final_status == "SUCCESS":
            ctx.completed_steps.add(self.name)

        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        return Outcome(final_status, ctx, collected_errors, duration_ms=duration)
