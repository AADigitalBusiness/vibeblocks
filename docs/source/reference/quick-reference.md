# Quick Reference

## Core Building Blocks

- `ExecutionContext[T]`: shared flow state and trace
- `Beat`: atomic executable step
- `Chain`: ordered group of steps
- `Flow`: orchestration boundary and failure strategy
- `SyncRunner` / `AsyncRunner`: execution engines

## Failure Strategies

- `ABORT`
- `CONTINUE`
- `COMPENSATE`

## Common Objects

- `RetryPolicy`
- `Outcome`
- `Event`

Use [API Reference](../api_reference.rst) for complete signatures.
