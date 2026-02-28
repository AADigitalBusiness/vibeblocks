import pytest
import asyncio
from functools import partial
from typing import Any
from taskchain.components.beat import Beat
from taskchain.core.context import ExecutionContext
from taskchain.runtime.runner import SyncRunner, AsyncRunner
from taskchain.utils.inspection import is_async_callable

async def async_fn(ctx):
    pass

class AsyncCallable:
    async def __call__(self, ctx):
        pass

def sync_fn(ctx):
    pass

class SyncCallable:
    def __call__(self, ctx):
        pass

def test_inspection_util():
    # Use dummy arguments for callables if needed, but inspect doesn't call them.
    assert is_async_callable(async_fn)
    assert is_async_callable(AsyncCallable())
    assert is_async_callable(partial(async_fn))
    assert is_async_callable(partial(AsyncCallable()))

    assert not is_async_callable(sync_fn)
    assert not is_async_callable(SyncCallable())
    assert not is_async_callable(partial(sync_fn))

def test_beat_async_detection():
    # No need for async context, just checking property

    t1 = Beat("t1", async_fn)
    assert t1.is_async, "Direct async function should be detected"

    t2 = Beat("t2", AsyncCallable())
    assert t2.is_async, "Async callable object should be detected"

    t3 = Beat("t3", partial(async_fn))
    assert t3.is_async, "Partial async function should be detected"

    t4 = Beat("t4", sync_fn)
    assert not t4.is_async, "Sync function should be detected as sync"

def test_beat_runtime_safety_sync():
    # If a function is sync but returns a coroutine (undetected async)
    # The beat should fail loudly.

    async def hidden_coro():
        pass

    def sneaky_fn(ctx):
        return hidden_coro()

    t = Beat("sneaky", sneaky_fn)
    # Correctly identified as sync function because 'sneaky_fn' is sync def
    assert not t.is_async

    ctx = ExecutionContext[dict](data={})
    runner = SyncRunner()

    # Running this sync should raise RuntimeError inside Beat because it returns awaitable
    # The Beat catches it and returns FAILED Outcome with BeatExecutionError wrapping RuntimeError
    outcome = runner.run(t, ctx)

    # outcome.errors[0] is BeatExecutionError wrapping RuntimeError
    assert outcome.status == "FAILED"
    assert len(outcome.errors) > 0
    # Search error message deep in cause or message
    error_msg = str(outcome.errors[0])
    if outcome.errors[0].__cause__:
        error_msg += str(outcome.errors[0].__cause__)

    assert "returned an awaitable" in error_msg
