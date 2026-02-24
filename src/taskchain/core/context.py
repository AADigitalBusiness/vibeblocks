"""
Core execution context structures.

This module provides the ExecutionContext class, which flows through 
all tasks and processes, accumulating data and tracking trace history.
"""

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, TypeVar, Literal, List, Dict, Any, Type, Optional, Set
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

        # Reconstruct Trace
        trace_data = parsed.get("trace", [])
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

        # Reconstruct Data
        raw_data = parsed.get("data")
        data_obj: Any = raw_data

        if data_cls and raw_data is not None:
            # 1. Try Pydantic v2 support
            if hasattr(data_cls, "model_validate"):
                try:
                    data_obj = data_cls.model_validate(raw_data)
                except Exception:
                    pass
            # 2. Try Pydantic v1 support
            elif hasattr(data_cls, "parse_obj"):
                try:
                    data_obj = data_cls.parse_obj(raw_data) # type: ignore
                except Exception:
                    pass
            # 3. Try standard Dataclass dictionary unpacking
            elif dataclasses.is_dataclass(data_cls) and isinstance(raw_data, dict):
                try:
                    data_obj = data_cls(**raw_data)
                except TypeError:
                    pass
            # 4. Fallback: Standard instantiation if signature matches dict keys
            elif isinstance(raw_data, dict):
                 try:
                     # Risky, but better than silent fail when someone uses typed dicts.
                     data_obj = data_cls(**raw_data)
                 except TypeError:
                     pass

        return cls(
            data=data_obj,
            trace=trace_objs,
            metadata=parsed.get("metadata", {}),
            completed_steps=set(parsed.get("completed_steps", []))
        )
