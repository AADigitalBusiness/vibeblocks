import pytest
from vibeblocks import Block, Chain, Flow, ExecutionContext
from vibeblocks.components.block import BlockTimeoutError
from vibeblocks.policies.retry import RetryPolicy
from vibeblocks.policies.failure import FailureStrategy
import time


def test_block_timeout():
    def slow_task(ctx):
        time.sleep(0.5)
        return "done"

    t = Block("slow", slow_task, timeout=0.1)
    ctx = ExecutionContext({})

    # execute() catches exception and returns Outcome(FAILED)
    outcome = t.execute(ctx)
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BlockTimeoutError)
               for e in outcome.errors)


def test_block_retry():
    attempts = 0

    def failing_logic(ctx):
        nonlocal attempts
        attempts += 1
        raise ValueError("Fail")

    t = Block("retry_block", failing_logic,
              retry_policy=RetryPolicy(max_attempts=3, delay=0.001))
    ctx = ExecutionContext({})
    outcome = t.execute(ctx)

    assert outcome.status == "FAILED"
    assert attempts == 3


def test_chain_execution():
    def step1(ctx):
        ctx.data["step1"] = True

    def step2(ctx):
        ctx.data["step2"] = True

    c = Chain("chain", [Block("s1", step1), Block("s2", step2)])
    ctx = ExecutionContext({})
    outcome = c.execute(ctx)

    assert outcome.status == "SUCCESS"
    assert ctx.data["step1"] is True
    assert ctx.data["step2"] is True


def test_flow_compensation():
    def step1(ctx):
        ctx.data["s1"] = "done"

    def undo1(ctx):
        ctx.data["s1"] = "undone"

    def step2(ctx):
        raise ValueError("Fail at step 2")

    t1 = Block("step1", step1, undo=undo1)
    t2 = Block("step2", step2)

    f = Flow("flow", [t1, t2], strategy=FailureStrategy.COMPENSATE)
    ctx = ExecutionContext({})

    outcome = f.execute(ctx)

    assert outcome.status == "FAILED"
    assert ctx.data["s1"] == "undone"
