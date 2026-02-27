"""
Utilities for generating JSON Schemas from Flow manifests and data models.
Designed to work with OpenAI Function Calling or similar LLM structured outputs.
"""

import dataclasses
import inspect
from typing import Any, Dict, List, Type, get_args, get_origin, Union

def generate_function_schema(flow_manifest: Dict[str, Any], context_model: Type[Any]) -> Dict[str, Any]:
    """
    Generates a JSON Schema for the Flow execution request.

    Args:
        flow_manifest: The dictionary returned by Flow.get_manifest().
        context_model: The class (Dataclass or Pydantic Model) used for ExecutionContext.data.

    Returns:
        A JSON Schema compatible with OpenAI Function Calling.
    """

    # 1. Generate Schema for the Context Data
    data_schema = _get_model_schema(context_model)

    # 2. Build the full parameters schema
    # We want the LLM to provide the data to initialize the context.
    parameters_schema = {
        "type": "object",
        "properties": {
            "initial_data": data_schema
        },
        "required": ["initial_data"]
    }

    # 3. Construct the function definition
    function_def = {
        "name": f"run_{flow_manifest['name'].lower().replace(' ', '_')}",
        "description": flow_manifest['description'],
        "parameters": parameters_schema
    }

    return function_def

def _get_model_schema(model: Type[Any]) -> Dict[str, Any]:
    """
    Extracts JSON Schema from a Pydantic model or Dataclass.
    """
    # 1. Pydantic v2
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()

    # 2. Pydantic v1
    if hasattr(model, "schema"):
        return model.schema()

    # 3. Dataclasses
    if dataclasses.is_dataclass(model):
        return _dataclass_to_schema(model)

    # 4. Fallback for simple types or dicts (limited support)
    return {"type": "object", "additionalProperties": True}

def _dataclass_to_schema(dc: Type[Any]) -> Dict[str, Any]:
    """
    Manually converts a dataclass to a simple JSON Schema.
    """
    properties = {}
    required = []

    for field in dataclasses.fields(dc):
        # field.type might be a string if "from __future__ import annotations" is used,
        # or a type object. This simple extractor assumes type object or simple forward ref.
        field_type = field.type
        prop_schema = _type_to_schema(field_type)
        properties[field.name] = prop_schema

        # Assume fields without default values are required
        if field.default == dataclasses.MISSING and field.default_factory == dataclasses.MISSING:
            required.append(field.name)

    return {
        "title": dc.__name__,
        "type": "object",
        "properties": properties,
        "required": required
    }

def _type_to_schema(py_type: Any) -> Dict[str, Any]:
    """
    Maps Python types to JSON Schema types.
    """
    if py_type == str:
        return {"type": "string"}
    if py_type == int:
        return {"type": "integer"}
    if py_type == float:
        return {"type": "number"}
    if py_type == bool:
        return {"type": "boolean"}

    # Handle Optional[T] -> Union[T, None]
    origin = get_origin(py_type)
    args = get_args(py_type)

    if origin is Union:
        # Simplification: take the first non-None type
        non_none_args = [arg for arg in args if arg is not type(None)]
        if non_none_args:
            return _type_to_schema(non_none_args[0])

    if origin is list or origin is List:
        item_schema = _type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item_schema}

    if origin is dict or origin is Dict:
        return {"type": "object"}

    # Handle nested dataclasses
    if dataclasses.is_dataclass(py_type):
        return _dataclass_to_schema(py_type)

    return {"type": "string"} # Default fallback
