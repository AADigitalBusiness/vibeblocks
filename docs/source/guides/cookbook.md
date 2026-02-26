# Cookbook

Canonical reference examples for the most common usage patterns.

## Scenarios Covered

1. Continue processing when one item fails (`FailureStrategy.CONTINUE`)
2. Retry unstable operations (`RetryPolicy`)
3. Share state between tasks using `ctx.data.*`

## Source File

- `examples/cookbook.py`

## Run

From repository root:

```bash
PYTHONPATH=src ./venv/bin/python examples/cookbook.py
```

