"""
TaskChain Cookbook: 3 canonical examples that cover common use cases.

Run:
    PYTHONPATH=src ./venv/bin/python examples/cookbook.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from taskchain import ExecutionContext, FailureStrategy, SyncRunner, Workflow, task
from taskchain.policies.retry import BackoffStrategy, RetryPolicy
from taskchain.utils.inspection import is_async_callable


def _prepare_task(task_obj: Any) -> Any:
    """
    Compatibility shim for local source checkouts where Task runtime flags
    may not be initialized yet.
    """

    if not hasattr(task_obj, "_is_async"):
        task_obj._is_async = is_async_callable(task_obj.func)
    if not hasattr(task_obj, "_is_undo_async"):
        task_obj._is_undo_async = bool(task_obj.undo and is_async_callable(task_obj.undo))
    return task_obj


@dataclass
class ImportBatch:
    """State used by the CONTINUE strategy example."""

    records: list[dict[str, Any]]
    imported_ids: list[str] = field(default_factory=list)
    failed_ids: list[str] = field(default_factory=list)


def run_continue_strategy_example() -> None:
    """
    Example 1:
    Import a list of records and continue even if one record fails.
    """

    data = ImportBatch(
        records=[
            {"id": "u-100", "email": "ana@example.com"},
            {"id": "u-101", "email": "bad-email", "should_fail": True},
            {"id": "u-102", "email": "sam@example.com"},
        ]
    )
    ctx = ExecutionContext(data=data)

    steps = []
    for record in data.records:
        # Keep one task per record so the workflow can continue step-by-step.
        @task(name=f"import_{record['id']}")
        def import_record(context: ExecutionContext[ImportBatch], row: dict[str, Any] = record) -> None:
            row_id = str(row["id"])
            if row.get("should_fail"):
                context.data.failed_ids.append(row_id)
                raise ValueError(f"Record {row_id} rejected by upstream validation")

            context.data.imported_ids.append(row_id)

        steps.append(_prepare_task(import_record))

    workflow = Workflow(
        name="ImportUsersContinueOnError",
        steps=steps,
        strategy=FailureStrategy.CONTINUE,
    )
    outcome = SyncRunner().run(workflow, ctx)

    print("\n[Example 1] CONTINUE strategy")
    print(f"Outcome status: {outcome.status}")
    print(f"Imported: {ctx.data.imported_ids}")
    print(f"Failed: {ctx.data.failed_ids}")
    print(f"Collected errors: {len(outcome.errors)}")


@dataclass
class HttpRequestState:
    """State used by the retry example."""

    attempts: int = 0
    payload: dict[str, Any] | None = None


def run_retry_policy_example() -> None:
    """
    Example 2:
    Simulate an unstable HTTP task that needs up to 3 attempts.
    """

    ctx = ExecutionContext(data=HttpRequestState())
    retry_policy = RetryPolicy(
        max_attempts=3,
        delay=0.05,
        backoff=BackoffStrategy.FIXED,
        retry_on=(ConnectionError,),
    )

    @task(name="fetch_remote_profile", retry_policy=retry_policy)
    def fetch_remote_profile(context: ExecutionContext[HttpRequestState]) -> None:
        context.data.attempts += 1

        # Simulate transient HTTP failures for the first 2 attempts.
        if context.data.attempts < 3:
            raise ConnectionError("503 Service Unavailable")

        context.data.payload = {"id": "u-200", "status": "ok"}

    workflow = Workflow(name="UnstableHttpWorkflow", steps=[_prepare_task(fetch_remote_profile)])
    outcome = SyncRunner().run(workflow, ctx)

    print("\n[Example 2] RetryPolicy")
    print(f"Outcome status: {outcome.status}")
    print(f"Attempts made: {ctx.data.attempts}")
    print(f"Payload: {ctx.data.payload}")


@dataclass
class SharedContextData:
    """State shared across tasks through ctx.data.* attributes."""

    raw_email: str = ""
    normalized_email: str = ""
    domain: str = ""


def run_shared_context_example() -> None:
    """
    Example 3:
    Share data between two tasks using ctx.data.*.
    """

    ctx = ExecutionContext(data=SharedContextData())

    @task(name="capture_email")
    def capture_email(context: ExecutionContext[SharedContextData]) -> None:
        context.data.raw_email = "  USER@Example.COM  "

    @task(name="normalize_email")
    def normalize_email(context: ExecutionContext[SharedContextData]) -> None:
        context.data.normalized_email = context.data.raw_email.strip().lower()
        context.data.domain = context.data.normalized_email.split("@")[1]

    workflow = Workflow(
        name="SharedContextWorkflow",
        steps=[_prepare_task(capture_email), _prepare_task(normalize_email)],
    )
    outcome = SyncRunner().run(workflow, ctx)

    print("\n[Example 3] Shared context (ctx.data.*)")
    print(f"Outcome status: {outcome.status}")
    print(f"Raw email: {ctx.data.raw_email!r}")
    print(f"Normalized email: {ctx.data.normalized_email!r}")
    print(f"Domain: {ctx.data.domain!r}")


def main() -> None:
    run_continue_strategy_example()
    run_retry_policy_example()
    run_shared_context_example()


if __name__ == "__main__":
    main()
