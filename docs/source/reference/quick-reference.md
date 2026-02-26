# Quick Reference

## Core Building Blocks

- `ExecutionContext[T]`: shared workflow state and trace
- `Task`: atomic executable step
- `Process`: ordered group of steps
- `Workflow`: orchestration boundary and failure strategy
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

