import pytest
import asyncio
import time
from taskchain.components.task import Task
from taskchain.core.context import ExecutionContext
from taskchain.core.errors import TaskTimeoutError
from taskchain.runtime.runner import SyncRunner, AsyncRunner
from taskchain.core.decorators import task

def test_sync_task_timeout():
    ctx = ExecutionContext(data={})

    @task(timeout=0.1)
    def slow_sync_task(ctx):
        time.sleep(0.5)
        return "Done"

    outcome = SyncRunner().run(slow_sync_task, ctx)
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, TaskTimeoutError) for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)

def test_async_task_timeout():
    ctx = ExecutionContext(data={})

    @task(timeout=0.1)
    async def slow_async_task(ctx):
        await asyncio.sleep(0.5)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(slow_async_task, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, TaskTimeoutError) for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)

def test_sync_task_no_timeout():
    ctx = ExecutionContext(data={})

    @task(timeout=0.5)
    def fast_sync_task(ctx):
        time.sleep(0.1)
        return "Done"

    outcome = SyncRunner().run(fast_sync_task, ctx)
    assert outcome.status == "SUCCESS"

def test_async_task_no_timeout():
    ctx = ExecutionContext(data={})

    @task(timeout=0.5)
    async def fast_async_task(ctx):
        await asyncio.sleep(0.1)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(fast_async_task, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "SUCCESS"
