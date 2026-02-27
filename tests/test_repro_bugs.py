import pytest
import time
from taskchain.utils import serialization
from taskchain.components.chain import Chain
from taskchain.core.executable import Executable
from taskchain.core.context import ExecutionContext
from taskchain.core.outcome import Outcome

class FailingStep(Executable):
    def __init__(self, name):
        self.name = name

    @property
    def is_async(self):
        return False

    def execute(self, ctx):
        raise ValueError("Boom")

    def compensate(self, ctx):
        pass

def test_serialization_set_and_exception():
    data = {"tags": {"a", "b"}, "error": ValueError("oops")}
    try:
        json_str = serialization.to_json(data)
        assert "a" in json_str
        assert "oops" in json_str
    except TypeError:
        pytest.fail("serialization.to_json failed on set or Exception")

def test_chain_exception_handling():
    # Use a raw executable that raises, not a Beat
    step = FailingStep("failing_step")
    p = Chain("failing_chain", [step])
    ctx = ExecutionContext({})

    # Chain.execute catches exceptions but currently re-raises ChainExecutionError
    # We want it to return Outcome(FAILED)

    try:
        result = p.execute(ctx)
        assert isinstance(result, Outcome)
        assert result.status == "FAILED"
        # Check if original error is preserved
        assert any("Boom" in str(e) for e in result.errors)
    except Exception as e:
        pytest.fail(f"Chain.execute raised exception instead of returning Outcome: {e}")

def test_chain_duration():
    class SlowStep(Executable):
        def __init__(self, name):
            self.name = name

        @property
        def is_async(self):
            return False

        def execute(self, ctx):
            time.sleep(0.1)
            return Outcome("SUCCESS", ctx)
        def compensate(self, ctx): pass

    step = SlowStep("slow_step")
    p = Chain("slow_chain", [step])
    ctx = ExecutionContext({})

    result = p.execute(ctx)
    assert result.duration_ms > 0

from taskchain.core.decorators import beat

def test_metadata_preservation():
    @beat(name="my_beat")
    def my_func(ctx: ExecutionContext):
        """My docstring."""
        pass

    assert my_func.__name__ == "my_func"
    assert my_func.__doc__ == "My docstring."
    assert my_func.name == "my_beat"
