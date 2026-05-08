import pytest
import dataclasses
from dataclasses import dataclass
from typing import Optional, Union
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
    nickname: Optional[str] = None


def test_flow_manifest():
    def block1(ctx): pass
    def block2(ctx): pass

    b1 = Block("b1", block1, description="First block")
    b2 = Block("b2", block2, description="Second block")

    flow = Flow("TestFlow", [b1, b2], description="A test flow")

    manifest = flow.get_manifest()

    assert manifest["name"] == "TestFlow"
    assert manifest["description"] == "A test flow"
    assert len(manifest["blocks"]) == 2
    assert manifest["blocks"][0]["name"] == "b1"
    assert manifest["blocks"][0]["description"] == "First block"


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
    assert "nickname" in data_props
    assert data_props["nickname"]["type"] == "string"

    required_fields = schema["parameters"]["properties"]["initial_data"]["required"]
    assert "user_id" in required_fields
    assert "email" in required_fields
    assert "nickname" not in required_fields


def test_vibeblocks_dynamic_execution():
    def add_one(ctx):
        ctx.data["val"] += 1

    blocks = {
        "add_one": Block("add_one", add_one)
    }

    json_req = {
        "name": "DynamicAdd",
        "blocks": ["add_one", "add_one"],
        "strategy": "ABORT"
    }

    # We cheat a bit here passing a dict instead of UserContext as initial_data
    # because ExecutionContext handles dicts fine.
    result = VibeBlocks.run_from_json(
        json_req, initial_data={"val": 0}, available_blocks=blocks)

    assert result.status == "SUCCESS"
    assert result.context.data["val"] == 2


def test_schema_optional_and_union_types():
    @dataclass
    class ComplexContext:
        mandatory_maybe: Optional[float] = dataclasses.field() # Required because no default
        maybe_int: Optional[int] = None
        maybe_str: Union[str, None] = "default"

    def dummy_block(ctx): pass
    b = Block("dummy", dummy_block)
    flow = Flow("ComplexFlow", [b], description="Complex schema test")

    schema = generate_function_schema(flow.get_manifest(), ComplexContext)
    data_props = schema["parameters"]["properties"]["initial_data"]["properties"]
    required_fields = schema["parameters"]["properties"]["initial_data"]["required"]

    assert data_props["maybe_int"]["type"] == "integer"
    assert data_props["maybe_str"]["type"] == "string"
    assert data_props["mandatory_maybe"]["type"] == "number"

    assert "maybe_int" not in required_fields
    assert "maybe_str" not in required_fields
    assert "mandatory_maybe" in required_fields
