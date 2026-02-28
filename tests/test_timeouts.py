import pytest
import asyncio
import time
from vibeblocks.components.block import Block
from vibeblocks.core.context import ExecutionContext
from vibeblocks.core.errors import BlockTimeoutError
from vibeblocks.runtime.runner import SyncRunner, AsyncRunner
from vibeblocks.core.decorators import block


def test_sync_block_timeout():
    ctx = ExecutionContext(data={})

    @block(timeout=0.1)
    def slow_sync_block(ctx):
        time.sleep(0.5)
        return "Done"

    outcome = SyncRunner().run(slow_sync_block, ctx)
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BlockTimeoutError)
               for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)


def test_async_block_timeout():
    ctx = ExecutionContext(data={})

    @block(timeout=0.1)
    async def slow_async_block(ctx):
        await asyncio.sleep(0.5)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(slow_async_block, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BlockTimeoutError)
               for e in outcome.errors)
    assert "timed out after 0.1s" in str(outcome.errors[0].__cause__)


def test_sync_block_no_timeout():
    ctx = ExecutionContext(data={})

    @block(timeout=0.5)
    def fast_sync_block(ctx):
        time.sleep(0.1)
        return "Done"

    outcome = SyncRunner().run(fast_sync_block, ctx)
    assert outcome.status == "SUCCESS"


def test_async_block_no_timeout():
    ctx = ExecutionContext(data={})

    @block(timeout=0.5)
    async def fast_async_block(ctx):
        await asyncio.sleep(0.1)
        return "Done"

    async def run_test():
        return await AsyncRunner().run(fast_async_block, ctx)

    outcome = asyncio.run(run_test())
    assert outcome.status == "SUCCESS"
