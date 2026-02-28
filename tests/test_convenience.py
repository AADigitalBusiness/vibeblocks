import pytest
from dataclasses import dataclass

from taskchain import execute_flow, beat, Flow
from taskchain.core.context import ExecutionContext

@dataclass
class MyData:
    value: int

@beat()
def add_one(ctx: ExecutionContext[MyData]):
    ctx.data.value += 1

@beat()
async def add_one_async(ctx: ExecutionContext[MyData]):
    ctx.data.value += 1

def test_execute_flow_sync():
    flow = Flow("sync_flow", [add_one])
    data = MyData(value=1)

    outcome = execute_flow(flow, data)

    assert outcome.status == "SUCCESS"
    assert outcome.context.data.value == 2

@pytest.mark.asyncio
async def test_execute_flow_async():
    flow = Flow("async_flow", [add_one_async])
    data = MyData(value=1)

    outcome = await execute_flow(flow, data, async_mode=True)

    assert outcome.status == "SUCCESS"
    assert outcome.context.data.value == 2

def test_execute_flow_sync_with_beat():
    # Test passing a beat directly instead of a flow
    data = MyData(value=10)
    outcome = execute_flow(add_one, data)

    assert outcome.status == "SUCCESS"
    assert outcome.context.data.value == 11

@pytest.mark.asyncio
async def test_execute_flow_async_with_beat():
    # Test passing an async beat directly
    data = MyData(value=10)
    outcome = await execute_flow(add_one_async, data, async_mode=True)

    assert outcome.status == "SUCCESS"
    assert outcome.context.data.value == 11
