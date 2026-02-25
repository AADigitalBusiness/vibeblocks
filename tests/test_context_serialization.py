import json
import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import pytest
from taskchain.core.context import ExecutionContext, Event

# Mock classes for Pydantic v1 and v2

class MockPydanticV2:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def model_validate(cls, data: dict):
        return cls(**data)

class MockPydanticV1:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def parse_obj(cls, data: dict):
        return cls(**data)

@dataclass
class StandardDataclass:
    field1: str
    field2: int

class PlainClass:
    def __init__(self, field1: str, field2: int):
        self.field1 = field1
        self.field2 = field2

def test_from_json_standard_dataclass():
    data = {"field1": "value", "field2": 123}
    json_str = json.dumps({"data": data})

    ctx = ExecutionContext.from_json(json_str, data_cls=StandardDataclass)
    assert isinstance(ctx.data, StandardDataclass)
    assert ctx.data.field1 == "value"
    assert ctx.data.field2 == 123

def test_from_json_pydantic_v2():
    data = {"field1": "v2", "field2": 456}
    json_str = json.dumps({"data": data})

    ctx = ExecutionContext.from_json(json_str, data_cls=MockPydanticV2)
    assert isinstance(ctx.data, MockPydanticV2)
    assert ctx.data.field1 == "v2"
    assert ctx.data.field2 == 456

def test_from_json_pydantic_v1():
    data = {"field1": "v1", "field2": 789}
    json_str = json.dumps({"data": data})

    ctx = ExecutionContext.from_json(json_str, data_cls=MockPydanticV1)
    assert isinstance(ctx.data, MockPydanticV1)
    assert ctx.data.field1 == "v1"
    assert ctx.data.field2 == 789

def test_from_json_plain_class_dict_unpacking():
    data = {"field1": "plain", "field2": 101}
    json_str = json.dumps({"data": data})

    ctx = ExecutionContext.from_json(json_str, data_cls=PlainClass)
    assert isinstance(ctx.data, PlainClass)
    assert ctx.data.field1 == "plain"
    assert ctx.data.field2 == 101

def test_from_json_no_data_cls():
    data = {"some": "data"}
    json_str = json.dumps({"data": data})

    ctx = ExecutionContext.from_json(json_str)
    assert ctx.data == data

def test_from_json_trace_reconstruction():
    ts_str = "2023-01-01T12:00:00+00:00"
    trace_data = [
        {"timestamp": ts_str, "level": "INFO", "source": "test", "message": "msg"}
    ]
    json_str = json.dumps({"data": {}, "trace": trace_data})

    ctx = ExecutionContext.from_json(json_str)
    assert len(ctx.trace) == 1
    event = ctx.trace[0]
    assert event.message == "msg"
    assert event.timestamp == datetime.fromisoformat(ts_str)

def test_from_json_completed_steps():
    steps = ["step1", "step2"]
    json_str = json.dumps({"data": {}, "completed_steps": steps})

    ctx = ExecutionContext.from_json(json_str)
    assert ctx.completed_steps == {"step1", "step2"}
