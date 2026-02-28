# VibeBlocks

**AI-First Orchestration for Python.**

VibeBlocks evolves the concept of task orchestration into an AI-ready framework. It maintains the "Zero-Gravity" architecture (no external dependencies) while introducing a Semantic Layer for LLM integration and dynamic flow generation.

## Key Concepts

1.  **Block:** The atomic unit of execution (formerly Task).
2.  **Chain:** A linear sequence of Blocks (formerly Process).
3.  **Flow:** High-level orchestrator with failure strategies (formerly Workflow).

## Installation

```bash
pip install vibeblocks
```

## Quick Start

### 1. Classic Usage

```python
from vibeblocks import Flow, ExecutionContext, block, execute_flow

# 1. Define your blocks with @block decorator
@block(description="Extracts data from source")
def extract(ctx: ExecutionContext):
    print("Extracting data...")
    ctx.data["raw"] = [1, 2, 3, 4, 5]
    return ctx.data["raw"]

@block(description="Doubles the input values")
def transform(ctx: ExecutionContext):
    print("Transforming data...")
    data = ctx.data["raw"]
    ctx.data['processed'] = [x * 2 for x in data]
    return ctx.data['processed']

@block(description="Loads data to destination")
def load(ctx: ExecutionContext):
    print(f"Loading data: {ctx.data['processed']}")
    return True

# 2. Create the Flow
pipeline = Flow("ETL_Flow", [extract, transform, load])

# 3. Execute
result = execute_flow(pipeline, data={})

if result.status == "SUCCESS":
    print("Flow completed successfully!")
else:
    print(f"Flow failed: {result.errors}")
```

### 2. AI-Driven Dynamic Flows

VibeBlocks allows LLMs to generate flows on the fly using JSON schemas.

```python
from vibeblocks.vibeblocks import VibeBlocks

# JSON definition (could come from an LLM)
flow_request = {
    "name": "DynamicETL",
    "steps": ["extract", "transform", "load"],
    "strategy": "ABORT"
}

# Available blocks registry
blocks_registry = {
    "extract": extract,
    "transform": transform,
    "load": load
}

# Execute dynamically
result = VibeBlocks.run_from_json(flow_request, initial_data={}, available_blocks=blocks_registry)
```

## License

MIT License. See [LICENSE](LICENSE) for details.
