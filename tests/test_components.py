import pytest
from taskchain import Beat, Chain, Flow, ExecutionContext
from taskchain.components.beat import BeatTimeoutError
from taskchain.policies.retry import RetryPolicy
from taskchain.policies.failure import FailureStrategy
import time

def test_beat_timeout():
    def slow_task(ctx):
        time.sleep(0.5)
        return "done"

    t = Beat("slow", slow_task, timeout=0.1)
    ctx = ExecutionContext({})

    # execute() catches exception and returns Outcome(FAILED)
    outcome = t.execute(ctx)
    assert outcome.status == "FAILED"
    assert any(isinstance(e.__cause__, BeatTimeoutError) for e in outcome.errors)

def test_beat_retry():
    attempts = 0
    def failing_logic(ctx):
        nonlocal attempts
        attempts += 1
        raise ValueError("Fail")

    t = Beat("retry_beat", failing_logic, retry_policy=RetryPolicy(max_attempts=3, delay=0.001))
    ctx = ExecutionContext({})
    outcome = t.execute(ctx)

    assert outcome.status == "FAILED"
    assert attempts == 3

def test_chain_execution():
    def step1(ctx):
        ctx.data["step1"] = True

    def step2(ctx):
        ctx.data["step2"] = True

    c = Chain("chain", [Beat("s1", step1), Beat("s2", step2)])
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

    t1 = Beat("step1", step1, undo=undo1)
    t2 = Beat("step2", step2)

    f = Flow("flow", [t1, t2], strategy=FailureStrategy.COMPENSATE)
    ctx = ExecutionContext({})

    outcome = f.execute(ctx)

    assert outcome.status == "FAILED"
    assert ctx.data["s1"] == "undone"
