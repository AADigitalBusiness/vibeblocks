import pytest
import asyncio
import time
from vibeflow.components.beat import Beat
from vibeflow.core.context import ExecutionContext
from vibeflow.core.errors import BeatTimeoutError
from vibeflow.runtime.runner import SyncRunner, AsyncRunner
from vibeflow.core.decorators import beat


def test_sync_beat_timeout():
    ctx = ExecutionContext(data={})

    @beat(timeout=0.1)
    def slow_sync_beat(ctx):
        time.sleep(0.5)
        return "Done"

    outcome = SyncRunner().run(slow_sync_beat, ctx)
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BeatTimeoutError)
               for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)


def test_async_beat_timeout():
    ctx = ExecutionContext(data={})

    @beat(timeout=0.1)
    async def slow_async_beat(ctx):
        await asyncio.sleep(0.5)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(slow_async_beat, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BeatTimeoutError)
               for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)


def test_sync_beat_no_timeout():
    ctx = ExecutionContext(data={})

    @beat(timeout=0.5)
    def fast_sync_beat(ctx):
        time.sleep(0.1)
        return "Done"

    outcome = SyncRunner().run(fast_sync_beat, ctx)
    assert outcome.status == "SUCCESS"


def test_async_beat_no_timeout():
    ctx = ExecutionContext(data={})

    @beat(timeout=0.5)
    async def fast_async_beat(ctx):
        await asyncio.sleep(0.1)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(fast_async_beat, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "SUCCESS"
