import json

import pytest

from vibeblocks.core.context import ExecutionContext


def test_from_json_invalid_structure():
    """Test deserialization with invalid top-level structure."""
    with pytest.raises(ValueError, match="Invalid JSON structure"):
        ExecutionContext.from_json("[]")

    with pytest.raises(ValueError, match="Invalid JSON structure"):
        ExecutionContext.from_json('"some string"')


def test_from_json_invalid_trace_type():
    """Test deserialization with invalid trace type."""
    json_str = json.dumps({"trace": "not_a_list"})
    with pytest.raises(ValueError, match="Invalid trace format"):
        ExecutionContext.from_json(json_str)


def test_from_json_invalid_metadata_type():
    """Test deserialization with invalid metadata type."""
    json_str = json.dumps({"metadata": "not_a_dict"})
    with pytest.raises(ValueError, match="Invalid metadata format"):
        ExecutionContext.from_json(json_str)


def test_from_json_invalid_completed_steps_type():
    """Test deserialization with invalid completed_steps type."""
    json_str = json.dumps({"completed_steps": "not_a_list"})
    with pytest.raises(ValueError, match="Invalid completed_steps format"):
        ExecutionContext.from_json(json_str)


def test_parse_trace_invalid_event_structure():
    """Test trace parsing with invalid event structure."""
    trace_data = [{"timestamp": "2023-01-01T12:00:00+00:00"}
                  ]  # Missing other fields
    json_str = json.dumps({"trace": trace_data})

    # Depending on implementation, this might raise KeyError or ValueError.
    # We aim for ValueError for better error reporting.
    with pytest.raises((KeyError, ValueError)):
        ExecutionContext.from_json(json_str)


def test_parse_trace_invalid_event_type():
    """Test trace parsing with invalid event type (not a dict)."""
    trace_data = ["not_a_dict"]
    json_str = json.dumps({"trace": trace_data})

    with pytest.raises(ValueError, match="Invalid trace event format"):
        ExecutionContext.from_json(json_str)
