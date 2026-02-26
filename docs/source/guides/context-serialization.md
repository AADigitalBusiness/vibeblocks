# How to Serialize and Restore Execution Context

## Goal

Persist workflow state for debugging, recovery, and transport.

## Workflow

1. Serialize context with `to_json()`.
2. Store the serialized payload.
3. Restore it with `from_json(...)` and optional `data_cls`.

## Reference

See [Getting Started](../getting_started.md) for examples.

