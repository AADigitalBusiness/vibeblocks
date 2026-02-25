# TaskChain

**A lightweight, framework-agnostic Python task orchestration library.**

TaskChain is designed for developers who need modular, simple, and maintainable pipelines without the overhead of heavy tools like Airflow or Luigi. It focuses on Developer Experience (DX), type safety, and "Zero-gravity" (no external dependencies).

## Why TaskChain?

*   **Simplicity First:** Define pipelines in pure Python. No DSLs, no complex configuration files.
*   **Lightweight:** Zero external dependencies. Just pure Python standard library.
*   **Modular:** Compose `Tasks` into `Processes` and `Workflows` (or `Chains`).
*   **Type Safe:** Built with modern Python typing in mind.
*   **Resilient:** Built-in retry policies and compensation logic (undo steps).

## Installation

```bash
pip install taskchain
```

## Quick Start

Create a simple pipeline to process data.

```python
from taskchain import Chain, Task, ExecutionContext

# 1. Define your tasks
def extract(ctx: ExecutionContext):
    print("Extracting data...")
    ctx.data["raw"] = [1, 2, 3, 4, 5]
    return ctx.data["raw"]

def transform(ctx: ExecutionContext):
    print("Transforming data...")
    data = ctx.data["raw"]
    ctx.data['processed'] = [x * 2 for x in data]
    return ctx.data['processed']

def load(ctx: ExecutionContext):
    print(f"Loading data: {ctx.data['processed']}")
    return True

# 2. Create the Chain (Workflow)
pipeline = Chain("ETL_Pipeline", [
    Task("Extract", extract),
    Task("Transform", transform),
    Task("Load", load)
])

# 3. Execute
initial_context = ExecutionContext(data={})
result = pipeline.execute(initial_context)

if result.status == "SUCCESS":
    print("Pipeline completed successfully!")
else:
    print(f"Pipeline failed: {result.errors}")
```

## TaskChain vs. Airflow/Luigi

| Feature | TaskChain | Airflow / Luigi |
| :--- | :--- | :--- |
| **Philosophy** | Library (embedded) | Platform (standalone service) |
| **Complexity** | Low (Pure Python) | High (Database, Scheduler, Web Server) |
| **Setup Time** | Seconds (`pip install`) | Hours (Docker, Config, DB init) |
| **Use Case** | Application logic, Data Scripts, ETL within apps | Enterprise Data Engineering, Cross-team dependencies |
| **Dependencies** | None (Standard Lib only) | Many (Databases, Providers, etc.) |

## License

MIT License. See [LICENSE](LICENSE) for details.
