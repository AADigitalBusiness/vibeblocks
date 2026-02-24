import inspect
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

    def execute(self, ctx: ExecutionContext[T]) -> Union[Outcome[T], Awaitable[Outcome[T]]]:
        if self._is_async_workflow():
             return self._execute_async(ctx)
        return self._execute_sync(ctx)

    def _is_async_workflow(self) -> bool:
        """Recursively checks if any step requires async execution."""
        for step in self.steps:
            if isinstance(step, Task):
                if inspect.iscoroutinefunction(step.func):
                    return True
            elif isinstance(step, Process):
                if step._is_async_workflow():
                    return True
            elif isinstance(step, Workflow):
                if step._is_async_workflow():
                    return True
        return False

    def _execute_sync(self, ctx: ExecutionContext[T]) -> Outcome[T]:
        ctx.log_event("INFO", self.name, "Workflow Started")
        collected_errors = []

        for step in self.steps:
            try:
                result = step.execute(ctx)

                # Check for async in sync context
                if inspect.isawaitable(result):
                    raise RuntimeError(f"Step '{getattr(step, 'name', 'Unknown')}' returned a coroutine in a sync workflow. Use AsyncRunner.")

                if isinstance(result, Outcome):
                    if result.status != "SUCCESS":
                        # Handle failure
                        if self.strategy == FailureStrategy.ABORT:
                            ctx.log_event("ERROR", self.name, f"Workflow Aborted due to failure in step '{getattr(step, 'name', 'Unknown')}'")
                            return Outcome("ABORTED", ctx, result.errors)

                        elif self.strategy == FailureStrategy.CONTINUE:
                            ctx.log_event("ERROR", self.name, f"Workflow Continuing after failure in step '{getattr(step, 'name', 'Unknown')}'")
                            collected_errors.extend(result.errors)
                            continue

                        elif self.strategy == FailureStrategy.COMPENSATE:
                            ctx.log_event("ERROR", self.name, f"Workflow Compensating due to failure in step '{getattr(step, 'name', 'Unknown')}'")
                            # If step is a Process, it might have partially succeeded
                            if isinstance(step, Process):
                                step.compensate(ctx)

                            self.compensate(ctx)
                            return Outcome("FAILED", ctx, result.errors)

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                collected_errors.append(e)

                if self.strategy == FailureStrategy.ABORT:
                    return Outcome("ABORTED", ctx, collected_errors)
                elif self.strategy == FailureStrategy.CONTINUE:
                    continue
                elif self.strategy == FailureStrategy.COMPENSATE:
                    if isinstance(step, Process):
                        step.compensate(ctx)
                    self.compensate(ctx)
                    return Outcome("FAILED", ctx, collected_errors)

        final_status: Literal["SUCCESS", "FAILED"] = "FAILED" if collected_errors else "SUCCESS"
        ctx.log_event("INFO", self.name, f"Workflow Completed with status {final_status}")
        return Outcome(final_status, ctx, collected_errors)

    async def _execute_async(self, ctx: ExecutionContext[T]) -> Outcome[T]:
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
                             return Outcome("ABORTED", ctx, result.errors)

                         elif self.strategy == FailureStrategy.CONTINUE:
                             ctx.log_event("ERROR", self.name, f"Workflow Continuing after failure")
                             collected_errors.extend(result.errors)
                             continue

                         elif self.strategy == FailureStrategy.COMPENSATE:
                             ctx.log_event("ERROR", self.name, f"Workflow Compensating due to failure")
                             if isinstance(step, Process):
                                 res = step.compensate(ctx)
                                 if inspect.isawaitable(res): await res

                             res = self.compensate(ctx)
                             if inspect.isawaitable(res): await res
                             return Outcome("FAILED", ctx, result.errors)

            except Exception as e:
                ctx.log_event("ERROR", self.name, f"Workflow Error: {str(e)}")
                collected_errors.append(e)

                if self.strategy == FailureStrategy.ABORT:
                    return Outcome("ABORTED", ctx, collected_errors)
                elif self.strategy == FailureStrategy.CONTINUE:
                    continue
                elif self.strategy == FailureStrategy.COMPENSATE:
                    if isinstance(step, Process):
                        res = step.compensate(ctx)
                        if inspect.isawaitable(res): await res

                    res = self.compensate(ctx)
                    if inspect.isawaitable(res): await res
                    return Outcome("FAILED", ctx, collected_errors)

        final_status: Literal["SUCCESS", "FAILED"] = "FAILED" if collected_errors else "SUCCESS"
        ctx.log_event("INFO", self.name, f"Workflow Completed with status {final_status}")
        return Outcome(final_status, ctx, collected_errors)

    def compensate(self, ctx: ExecutionContext[T]) -> Union[None, Awaitable[None]]:
        if self._is_async_workflow():
            return self._compensate_async(ctx)

        ctx.log_event("INFO", self.name, "Compensating Workflow")
        for step in reversed(self.steps):
            if self._did_step_succeed(ctx, step):
                step.compensate(ctx)
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

        for event in reversed(ctx.trace):
            if event.source == name and event.message.endswith("Completed"):
                return True
        return False
