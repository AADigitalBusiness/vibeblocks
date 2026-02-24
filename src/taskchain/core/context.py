import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, TypeVar, Literal, List, Dict, Any, Type, Optional
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
        return serialization.to_json(self)

    @classmethod
    def from_json(cls, raw: str, data_cls: Optional[Type[T]] = None) -> "ExecutionContext[T]":
        """
        Deserializes a JSON string back to an ExecutionContext.

        Args:
            raw: The JSON string.
            data_cls: Optional class to cast the 'data' field into (e.g. a dataclass).
                      If not provided, 'data' remains a dictionary.
        """
        parsed = serialization.from_json(raw)

        # Reconstruct Trace
        trace_data = parsed.get("trace", [])
        trace_objs = []
        for e in trace_data:
            ts_str = e["timestamp"]
            # Handle ISO format. datetime.fromisoformat is robust enough for isoformat() output.
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                ts = datetime.now(timezone.utc) # Fallback if parsing fails

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
             if dataclasses.is_dataclass(data_cls) and isinstance(raw_data, dict):
                 try:
                     data_obj = data_cls(**raw_data)
                 except TypeError:
                     # If fields don't match, keep as dict
                     pass

        return cls(
            data=data_obj,
            trace=trace_objs,
            metadata=parsed.get("metadata", {})
        )
