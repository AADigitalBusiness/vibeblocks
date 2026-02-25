import dataclasses
import json
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, TypeVar, Union

T = TypeVar("T")

def _default_encoder(obj: Any) -> Any:
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, Exception):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Enum):
        return obj.value
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    # Let standard json encoder raise the error or handle basic types
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def to_json(obj: Any, indent: int | None = 2) -> str:
    """Serializes an object to a JSON string using custom encoders."""
    return json.dumps(obj, default=_default_encoder, indent=indent)

def from_json(json_str: str) -> Any:
    """Deserializes a JSON string to a dictionary/list structure."""
    return json.loads(json_str)
