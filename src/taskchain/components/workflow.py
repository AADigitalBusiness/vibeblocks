"""
Workflow orchestrator for executing trees of Tasks and Processes.
Handles high-level failure policies.
"""

import inspect
import time
from typing import List, Union, Awaitable, TypeVar, Literal

from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome
from taskchain.core.executable import Executable
from taskchain.policies.failure import FailureStrategy
from taskchain.components.task import Task
from taskchain.components.process import Process

T = TypeVar("T")

class Workflow(Executable[T]):
    """
    The top-level orchestrator that manages a sequence of steps (Tasks or Processes)
    and handles failures according to a strategy.
    """
    def __init__(self, name: str, steps: List[Executable[T]], strategy: FailureStrategy = FailureStrategy.ABORT):
        self.name = name
        self.steps = steps
        self.strategy = strategy

    @property
    def is_async(self) -> bool:
        """Recursively checks if any step requires async execution."""
        return any(step.is_async for step in self.steps)

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self.is_async:
             return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Workflow Started")
        collected_errors = []

        for step in self.steps:
            try:
                result = step.execute(ctx)

                # Check for async in sync context
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned a coroutine in a sync workflow. Use AsyncRunner.")

                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                        # Handle failure
                        if self.strategy == FailureStrategy.ABORT:
                            ctx.log_event("ERROR", self.name, f"Workflow Aborted due to failure in step '{getattr(step, 'name', 'Unknown')}'")
                            duration = (time.perf_counter_ns() - start_time) // 1_000_000
                            return Outcome("ABORTED", ctx, result.errors, duration_ms=duration)

                        elif self.strategy == FailureStrategy.CONTINUE:
                            ctx.log_event("ERROR", self.name, f"Workflow Continuing after failure in step '{getattr(step, 'name', 'Unknown')}'")
                            collected_errors.extend(result.errors)
                            continue

                        elif self.strategy == FailureStrategy.COMPENSATE:
                            ctx.log_event("ERROR", self.name, f"Workflow Compensating due to failure in step '{getattr(step, 'name', 'Unknown')}'")
                            
                            # Compensate the current failing step (it handles its own partial state natively)
                            res = step.compensate(ctx)
                            if inspect.isawaitable(res):
                                if inspect.iscoroutine(res):
                                    res.close()
                                raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned an async compensation in a sync workflow. Use AsyncRunner.")

                            # Compensate previous steps
                            self.compensate(ctx)
                            duration = (time.perf_counter_ns() - start_time) // 1_000_000
                            return Outcome("FAILED", ctx, result.errors, duration_ms=duration)

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                collected_errors.append(e)

                if self.strategy == FailureStrategy.ABORT:
                    duration = (time.perf_counter_ns() - start_time) // 1_000_000
                    return Outcome("ABORTED", ctx, collected_errors, duration_ms=duration)
                elif self.strategy == FailureStrategy.CONTINUE:
                    continue
                elif self.strategy == FailureStrategy.COMPENSATE:
                    res = step.compensate(ctx)
                    if inspect.isawaitable(res):
                        if inspect.iscoroutine(res):
                            res.close()
                        raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned an async compensation in a sync workflow. Use AsyncRunner.")
                        
                    self.compensate(ctx)
                    duration = (time.perf_counter_ns() - start_time) // 1_000_000
                    return Outcome("FAILED", ctx, collected_errors, duration_ms=duration)

        final_status: Literal["SUCCESS", "FAILED"] = "FAILED" if collected_errors else "SUCCESS"
        ctx.log_event("INFO", self.name, f"Workflow Completed with status {final_status}")
        
        if final_status == "SUCCESS":
            ctx.completed_steps.add(self.name)
            
        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        return Outcome(final_status, ctx, collected_errors, duration_ms=duration)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        start_time = time.perf_counter_ns()
        ctx.log_event("INFO", self.name, "Workflow Started (Async)")
        collected_errors = []

        for step in self.steps:
            try:
                result = step.execute(ctx)
                if inspect.isawaitable(result):
                    result = await result

                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                         if self.strategy == FailureStrategy.ABORT:
                             ctx.log_event("ERROR", self.name, f"Workflow Aborted due to failure")
                             duration = (time.perf_counter_ns() - start_time) // 1_000_000
                             return Outcome("ABORTED", ctx, result.errors, duration_ms=duration)

                         elif self.strategy == FailureStrategy.CONTINUE:
                             ctx.log_event("ERROR", self.name, f"Workflow Continuing after failure")
                             collected_errors.extend(result.errors)
                             continue

                         elif self.strategy == FailureStrategy.COMPENSATE:
                             ctx.log_event("ERROR", self.name, f"Workflow Compensating due to failure")
                             
                             res = step.compensate(ctx)
                             if inspect.isawaitable(res): await res

                             res = self.compensate(ctx)
                             if inspect.isawaitable(res): await res
                             duration = (time.perf_counter_ns() - start_time) // 1_000_000
                             return Outcome("FAILED", ctx, result.errors, duration_ms=duration)

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                collected_errors.append(e)

                if self.strategy == FailureStrategy.ABORT:
                    duration = (time.perf_counter_ns() - start_time) // 1_000_000
                    return Outcome("ABORTED", ctx, collected_errors, duration_ms=duration)
                elif self.strategy == FailureStrategy.CONTINUE:
                    continue
                elif self.strategy == FailureStrategy.COMPENSATE:
                    res = step.compensate(ctx)
                    if inspect.isawaitable(res): await res

                    res = self.compensate(ctx)
                    if inspect.isawaitable(res): await res
                    duration = (time.perf_counter_ns() - start_time) // 1_000_000
                    return Outcome("FAILED", ctx, collected_errors, duration_ms=duration)

        final_status: Literal["SUCCESS", "FAILED"] = "FAILED" if collected_errors else "SUCCESS"
        ctx.log_event("INFO", self.name, f"Workflow Completed with status {final_status}")
        
        if final_status == "SUCCESS":
            ctx.completed_steps.add(self.name)
            
        duration = (time.perf_counter_ns() - start_time) // 1_000_000
        return Outcome(final_status, ctx, collected_errors, duration_ms=duration)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self.is_async:
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Workflow")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                res = step.compensate(ctx)
                if inspect.isawaitable(res):
                    if inspect.iscoroutine(res):
                        res.close()
                    raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned an async compensation in a sync workflow. Use AsyncRunner.")
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
