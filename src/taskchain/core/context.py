"""
Core execution context structures.

This module provides the ExecutionContext class, which flows through 
all tasks and processes, accumulating data and tracking trace history.
"""

import dataclasses
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Literal, Optional, Set, Type, TypeVar

from taskchain.utils import serialization

T = TypeVar("T")

@dataclass
class Event:
    timestamp: datetime
    level: Literal["INFO", "ERROR", "DEBUG"]
    source: str
    message: str

@dataclass
class ExecutionContext(Generic[T]):
    data: T
    trace: List[Event] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_steps: Set[str] = field(default_factory=set)

    def log_event(self, level: Literal["INFO", "ERROR", "DEBUG"], source: str, message: str) -> None:
        """Logs an event to the trace."""
        self.trace.append(Event(
            timestamp=datetime.now(timezone.utc),
            level=level,
            source=source,
            message=message
        ))

    def to_json(self) -> str:
        """Serializes the context to a JSON string."""
        # Convert completed_steps (set) to list for JSON serialization before calling custom util
        # Since to_json uses a default encoder, we can also add set handling there,
        # but the safest local way is:
        serializable_self = {
            "data": self.data,
            "trace": self.trace,
            "metadata": self.metadata,
            "completed_steps": list(self.completed_steps)
        }
        return serialization.to_json(serializable_self)

    @staticmethod
    def _parse_trace(trace_data: List[Dict[str, Any]]) -> List[Event]:
        trace_objs = []
        for e in trace_data:
            ts_str = e["timestamp"]
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                ts = datetime.now(timezone.utc)

            trace_objs.append(Event(
                timestamp=ts,
                level=e["level"],
                source=e["source"],
                message=e["message"]
            ))
        return trace_objs

    @staticmethod
    def _parse_data(raw_data: Any, data_cls: Optional[Type[T]] = None) -> T:
        if not data_cls or raw_data is None:
            return raw_data

        # 1. Try Pydantic v2 support
        if hasattr(data_cls, "model_validate"):
            try:
                return data_cls.model_validate(raw_data)
            except Exception as e:
                warnings.warn(f"Failed to deserialize using Pydantic v2 model_validate: {e}", RuntimeWarning)
                return raw_data

        # 2. Try Pydantic v1 support
        if hasattr(data_cls, "parse_obj"):
            try:
                return data_cls.parse_obj(raw_data)  # type: ignore
            except Exception as e:
                warnings.warn(f"Failed to deserialize using Pydantic v1 parse_obj: {e}", RuntimeWarning)
                return raw_data

        # 3. Try standard Dataclass dictionary unpacking
        if dataclasses.is_dataclass(data_cls) and isinstance(raw_data, dict):
            try:
                return data_cls(**raw_data)
            except TypeError as e:
                warnings.warn(f"Failed to deserialize dataclass: {e}", RuntimeWarning)
                return raw_data

        # 4. Fallback: Standard instantiation if signature matches dict keys
        if isinstance(raw_data, dict):
            try:
                # Risky, but better than silent fail when someone uses typed dicts.
                return data_cls(**raw_data)
            except TypeError as e:
                warnings.warn(f"Failed to deserialize using standard instantiation: {e}", RuntimeWarning)
                return raw_data

        return raw_data

    @classmethod
    def from_json(cls, raw: str, data_cls: Optional[Type[T]] = None) -> "ExecutionContext[T]":
        """
        Deserializes a JSON string back to an ExecutionContext.

        Args:
            raw: The JSON string.
            data_cls: Optional class to cast the 'data' field into (e.g. a dataclass or Pydantic model).
                      If not provided, 'data' remains a dictionary.
        """
        parsed = serialization.from_json(raw)

        trace_objs = cls._parse_trace(parsed.get("trace", []))
        data_obj = cls._parse_data(parsed.get("data"), data_cls)

        return cls(
            data=data_obj,
            trace=trace_objs,
            metadata=parsed.get("metadata", {}),
            completed_steps=set(parsed.get("completed_steps", []))
        )
