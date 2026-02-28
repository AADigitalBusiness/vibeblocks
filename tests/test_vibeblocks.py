import pytest
from dataclasses import dataclass
from typing import Optional
from vibeblocks.components.block import Block
from vibeblocks.components.flow import Flow
from vibeblocks.utils.schema import generate_function_schema
from vibeblocks.vibeblocks import VibeBlocks
from vibeblocks.core.context import ExecutionContext


@dataclass
class UserContext:
    user_id: int
    email: str
    active: bool = False


def test_flow_manifest():
    def block1(ctx): pass
    def block2(ctx): pass

    b1 = Block("b1", block1, description="First block")
    b2 = Block("b2", block2, description="Second block")

    flow = Flow("TestFlow", [b1, b2], description="A test flow")

    manifest = flow.get_manifest()

    assert manifest["name"] == "TestFlow"
    assert manifest["description"] == "A test flow"
    assert len(manifest["steps"]) == 2
    assert manifest["steps"][0]["name"] == "b1"
    assert manifest["steps"][0]["description"] == "First block"


def test_schema_generation():
    def block1(ctx): pass
    b1 = Block("b1", block1)
    flow = Flow("SchemaFlow", [b1], description="Schema test")

    schema = generate_function_schema(flow.get_manifest(), UserContext)

    assert schema["name"] == "run_schemaflow"
    assert "initial_data" in schema["parameters"]["properties"]

    data_props = schema["parameters"]["properties"]["initial_data"]["properties"]
    assert "user_id" in data_props
    assert "email" in data_props


def test_vibeblocks_dynamic_execution():
    def add_one(ctx):
        ctx.data["val"] += 1

    blocks = {
        "add_one": Block("add_one", add_one)
    }

    json_req = {
        "name": "DynamicAdd",
        "steps": ["add_one", "add_one"],
        "strategy": "ABORT"
    }

    # We cheat a bit here passing a dict instead of UserContext as initial_data
    # because ExecutionContext handles dicts fine.
    result = VibeBlocks.run_from_json(
        json_req, initial_data={"val": 0}, available_blocks=blocks)

    assert result.status == "SUCCESS"
    assert result.context.data["val"] == 2
