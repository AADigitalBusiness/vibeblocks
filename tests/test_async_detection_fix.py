import pytest
import asyncio
from functools import partial
from typing import Any
from vibeblocks.components.block import Block
from vibeblocks.core.context import ExecutionContext
from vibeblocks.runtime.runner import SyncRunner, AsyncRunner
from vibeblocks.utils.inspection import is_async_callable


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


def test_block_async_detection():
    # No need for async context, just checking property

    t1 = Block("t1", async_fn)
    assert t1.is_async, "Direct async function should be detected"

    t2 = Block("t2", AsyncCallable())
    assert t2.is_async, "Async callable object should be detected"

    t3 = Block("t3", partial(async_fn))
    assert t3.is_async, "Partial async function should be detected"

    t4 = Block("t4", sync_fn)
    assert not t4.is_async, "Sync function should be detected as sync"


def test_block_runtime_safety_sync():
    # If a function is sync but returns a coroutine (undetected async)
    # The block should fail loudly.

    async def hidden_coro():
        pass

    def sneaky_fn(ctx):
        return hidden_coro()

    t = Block("sneaky", sneaky_fn)
    # Correctly identified as sync function because 'sneaky_fn' is sync def
    assert not t.is_async

    ctx = ExecutionContext[dict](data={})
    runner = SyncRunner()

    # Running this sync should raise RuntimeError inside Block because it returns awaitable
    # The Block catches it and returns FAILED Outcome with BlockExecutionError wrapping RuntimeError
    outcome = runner.run(t, ctx)

    # outcome.errors[0] is BlockExecutionError wrapping RuntimeError
    assert outcome.status == "FAILED"
    assert len(outcome.errors) > 0
    # Search error message deep in cause or message
    error_msg = str(outcome.errors[0])
    if outcome.errors[0].__cause__:
        error_msg += str(outcome.errors[0].__cause__)

    assert "returned an awaitable" in error_msg
