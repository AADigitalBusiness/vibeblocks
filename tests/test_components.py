import pytest
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from taskchain.components.task import Task
from taskchain.components.process import Process
from taskchain.components.workflow import Workflow
from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome
from taskchain.policies.retry import RetryPolicy
from taskchain.policies.failure import FailureStrategy
from taskchain.runtime.runner import SyncRunner, AsyncRunner
from taskchain.core.decorators import task

@dataclass
class SimpleData:
    count: int = 0
    history: List[str] = field(default_factory=list)

def test_task_success():
    data = SimpleData(count=0)
    ctx = ExecutionContext(data=data)

    @task()
    def increment(ctx):
        ctx.data.count += 1

    outcome = SyncRunner().run(increment, ctx)
    assert outcome.status == "SUCCESS"
    assert ctx.data.count == 1
    assert len(ctx.trace) >= 2 # Started, Completed

def test_task_retry():
    data = SimpleData(count=0)
    ctx = ExecutionContext(data=data)
    attempts = 0

    def failing_logic(ctx):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Fail")
        ctx.data.count = 100

    # Use small delay to speed up test
    t = Task("retry_task", failing_logic, retry_policy=RetryPolicy(max_attempts=3, delay=0.001))
    outcome = SyncRunner().run(t, ctx)

    assert outcome.status == "SUCCESS"
    assert attempts == 3
    assert ctx.data.count == 100
    assert any("Retrying" in e.message for e in ctx.trace)

def test_workflow_compensate():
    data = SimpleData(count=0)
    ctx = ExecutionContext(data=data)

    def step1(ctx):
        ctx.data.count += 10
        ctx.data.history.append("step1")
    def undo1(ctx):
        ctx.data.count -= 10
        ctx.data.history.append("undo1")

    def step2(ctx):
        raise ValueError("Step 2 Failed")

    t1 = Task("step1", step1, undo=undo1)
    t2 = Task("step2", step2)

    wf = Workflow("wf", [t1, t2], strategy=FailureStrategy.COMPENSATE)

    outcome = SyncRunner().run(wf, ctx)

    assert outcome.status == "FAILED"
    assert ctx.data.count == 0 # 10 added, then removed
    assert "step1" in ctx.data.history
    assert "undo1" in ctx.data.history

def test_process_bubbling():
    data = SimpleData()
    ctx = ExecutionContext(data=data)

    def fail(ctx): raise ValueError("Fail")
    t = Task("fail", fail)
    p = Process("proc", [t])

    # Process bubbles the FAILED Outcome from the Task
    outcome = SyncRunner().run(p, ctx)
    assert outcome.status == "FAILED"
    assert len(outcome.errors) > 0

def test_workflow_abort():
    data = SimpleData()
    ctx = ExecutionContext(data=data)

    def step1(ctx): ctx.data.count += 1
    def step2(ctx): raise ValueError("Fail")

    wf = Workflow("wf", [Task("s1", step1), Task("s2", step2)], strategy=FailureStrategy.ABORT)
    outcome = SyncRunner().run(wf, ctx)

    assert outcome.status == "ABORTED"
    assert ctx.data.count == 1
    assert len(outcome.errors) > 0

def test_async_runner_manual():
    # Manual async test wrapper without pytest-asyncio
    data = SimpleData()
    ctx = ExecutionContext(data=data)

    @task()
    async def async_inc(ctx):
        await asyncio.sleep(0.001)
        ctx.data.count += 1

    async def run_test():
        return await AsyncRunner().run(async_inc, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "SUCCESS"
    assert ctx.data.count == 1
