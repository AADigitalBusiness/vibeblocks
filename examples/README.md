# TaskChain Examples

This folder contains canonical examples that cover common TaskChain usage.

## Cookbook

Use `cookbook.py` to run three base scenarios:

1. Continue importing records when one record fails (`FailureStrategy.CONTINUE`)
2. Retry an unstable HTTP-like task up to 3 attempts (`RetryPolicy`)
3. Share data between tasks with `ctx.data.*`

Run from repository root:

```bash
PYTHONPATH=src ./venv/bin/python examples/cookbook.py
```

