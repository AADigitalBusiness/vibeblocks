import json
from dataclasses import dataclass
from datetime import datetime, timezone
from vibeflow.core.context import ExecutionContext, Event


@dataclass
class UserData:
    email: str
    user_id: str | None = None
    status: str = "pending"


def test_context_serialization():
    data = UserData(email="test@example.com", user_id="123")
    ctx = ExecutionContext[UserData](data=data)
    ctx.log_event("INFO", "test", "message")

    json_str = ctx.to_json()
    assert "test@example.com" in json_str
    assert "message" in json_str

    # Reload
    new_ctx = ExecutionContext[UserData].from_json(json_str, data_cls=UserData)
    assert isinstance(new_ctx.data, UserData)
    assert new_ctx.data.email == "test@example.com"
    assert len(new_ctx.trace) == 1
    assert new_ctx.trace[0].message == "message"
    assert isinstance(new_ctx.trace[0].timestamp, datetime)


def test_context_log_event():
    ctx = ExecutionContext[dict](data={})
    ctx.log_event("ERROR", "src", "msg")
    assert len(ctx.trace) == 1
    assert ctx.trace[0].level == "ERROR"
    assert ctx.trace[0].source == "src"
