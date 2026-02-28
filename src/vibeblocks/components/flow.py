"""
Flow orchestrator for executing trees of Blocks and Chaines.
Handles high-level failure policies.
"""

import inspect
import time
from typing import Any, Awaitable, Dict, List, Literal, Optional, Tuple, TypeVar, Union

from vibeblocks.core.context import ExecutionContext
from vibeblocks.core.executable import Executable
from vibeblocks.core.outcome import Outcome
from vibeblocks.policies.failure import FailureStrategy

T = TypeVar("T")


class Flow(Executable[T]):
    """
    The top-level orchestrator that manages a sequence of steps (Blocks or Chaines)
    and handles failures according to a strategy.
    """

    def __init__(
        self,
        name: str,
        steps: List[Executable[T]],
        description: Optional[str] = None,
        strategy: FailureStrategy = FailureStrategy.ABORT
    ):
        self.name = name
        self.steps = list(steps)
        self.description = description
        self.strategy = strategy
        self._is_async = any(step.is_async for step in self.steps)

    @property
    def is_async(self) -> bool:
        """Recursively checks if any step requires async execution."""
        return self._is_async

    def get_manifest(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the flow structure, including semantic descriptions.
        """
        steps_info = []
        for step in self.steps:
            step_data = {
                "name": getattr(step, "name", "Unknown"),
                "type": step.__class__.__name__,
                "description": getattr(step, "description", None) or step.__doc__ or "No description provided."
            }
            steps_info.append(step_data)

        return {
            "name": self.name,
            "description": self.description or "No description provided.",
            "steps": steps_info,
            "strategy": self.strategy.name
        }

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
            return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Flow Started")
        collected_errors = []

        for step in self.steps:
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
                            res, getattr(
                                step, "name", "Unknown"), "step compensation"
                        )
                        self.compensate(ctx)
                        if outcome:
                            outcome.duration_ms = (
                                time.perf_counter_ns() - start_time
                            ) // 1_000_000
                        return outcome

            except Exception as e:
                ctx.log_event("ERROR", self.name,
                              f"Flow Error: {ctx.format_exception(e)}")
                action, outcome = self._handle_failure_strategy(
                    ctx, step, [e], start_time
                )
                if action == "ABORT":
                    return outcome
                elif action == "CONTINUE":
                    collected_errors.append(e)
                    continue
                elif action == "COMPENSATE":
                    res = step.compensate(ctx)
                    self._ensure_not_awaitable(
                        res, getattr(
                            step, "name", "Unknown"), "step compensation"
                    )
                    res = self.compensate(ctx)
                    self._ensure_not_awaitable(
                        res, self.name, "flow compensation")
                    if outcome:
                        outcome.duration_ms = (
                            time.perf_counter_ns() - start_time
                        ) // 1_000_000
                    return outcome

        return self._finish_flow(ctx, collected_errors, start_time)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Flow Started (Async)")
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
                ctx.log_event("ERROR", self.name,
                              f"Flow Error: {ctx.format_exception(e)}")
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

        return self._finish_flow(ctx, collected_errors, start_time)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.is_async:
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Flow")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                self._ensure_not_awaitable(
                    res, getattr(step, "name", "Unknown"), "compensation"
                )
        return None

    async def _compensate_async(self, ctx: ExecutionContext[T]) -> None:
        ctx.log_event("INFO", self.name, "Compensating Flow (Async)")
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
                f"in a sync flow ({context}). Use AsyncRunner."
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
                f"Flow Aborted due to failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            duration = (time.perf_counter_ns() - start_time) // 1_000_000
            return "ABORT", Outcome("ABORTED", ctx, errors, duration_ms=duration)

        elif self.strategy == FailureStrategy.CONTINUE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Flow Continuing after failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            return "CONTINUE", None

        elif self.strategy == FailureStrategy.COMPENSATE:
            ctx.log_event(
                "ERROR",
                self.name,
                f"Flow Compensating due to failure in step '{getattr(step, 'name', 'Unknown')}'",
            )
            duration = (time.perf_counter_ns() - start_time) // 1_000_000
            return "COMPENSATE", Outcome("FAILED", ctx, errors, duration_ms=duration)

        return "CONTINUE", None

    def _finish_flow(
        self, ctx: ExecutionContext[T], collected_errors: List[Exception], start_time: int
    ) -> Outcome[T]:
        final_status: Literal["SUCCESS", "FAILED"] = (
            "FAILED" if collected_errors else "SUCCESS"
        )
        ctx.log_event("INFO", self.name,
                      f"Flow Completed with status {final_status}")

        if final_status == "SUCCESS":
            ctx.completed_steps.add(self.name)

        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        return Outcome(final_status, ctx, collected_errors, duration_ms=duration)
