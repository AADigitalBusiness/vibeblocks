import pytest
from dataclasses import dataclass
from typing import Optional
from vibeflow.components.beat import Beat
from vibeflow.components.flow import Flow
from vibeflow.utils.schema import generate_function_schema
from vibeflow.vibeflow import VibeFlow
from vibeflow.core.context import ExecutionContext


@dataclass
class UserContext:
    user_id: int
    email: str
    active: bool = False


def test_flow_manifest():
    def beat1(ctx): pass
    def beat2(ctx): pass

    b1 = Beat("b1", beat1, description="First beat")
    b2 = Beat("b2", beat2, description="Second beat")

    flow = Flow("TestFlow", [b1, b2], description="A test flow")

    manifest = flow.get_manifest()

    assert manifest["name"] == "TestFlow"
    assert manifest["description"] == "A test flow"
    assert len(manifest["steps"]) == 2
    assert manifest["steps"][0]["name"] == "b1"
    assert manifest["steps"][0]["description"] == "First beat"


def test_schema_generation():
    def beat1(ctx): pass
    b1 = Beat("b1", beat1)
    flow = Flow("SchemaFlow", [b1], description="Schema test")

    schema = generate_function_schema(flow.get_manifest(), UserContext)

    assert schema["name"] == "run_schemaflow"
    assert "initial_data" in schema["parameters"]["properties"]

    data_props = schema["parameters"]["properties"]["initial_data"]["properties"]
    assert "user_id" in data_props
    assert "email" in data_props


def test_vibeflow_dynamic_execution():
    def add_one(ctx):
        ctx.data["val"] += 1

    beats = {
        "add_one": Beat("add_one", add_one)
    }

    json_req = {
        "name": "DynamicAdd",
        "steps": ["add_one", "add_one"],
        "strategy": "ABORT"
    }

    # We cheat a bit here passing a dict instead of UserContext as initial_data
    # because ExecutionContext handles dicts fine.
    result = VibeFlow.run_from_json(
        json_req, initial_data={"val": 0}, available_beats=beats)

    assert result.status == "SUCCESS"
    assert result.context.data["val"] == 2
