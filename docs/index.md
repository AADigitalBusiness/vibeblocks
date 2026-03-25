---
hide:
  - navigation
  - toc
---

# VibeBlocks

**AI-First Workflow Orchestration for Python.**

Zero dependencies. Sync & async. Built for the age of AI agents.

---

## Why VibeBlocks?

<div class="grid cards" markdown>

-   :material-lightning-bolt:{ .lg .middle } **Zero Dependencies**

    ---

    Pure Python stdlib. No heavy frameworks, no lock-in. Drop it into any project.

-   :material-refresh:{ .lg .middle } **Retry-Ready**

    ---

    Per-block retry policies with FIXED, LINEAR, and EXPONENTIAL backoff, jitter, and per-exception routing.

-   :material-undo-variant:{ .lg .middle } **Saga Compensation**

    ---

    Every block can define an `undo`. On failure, completed steps roll back in reverse order automatically.

-   :material-code-braces:{ .lg .middle } **Sync & Async**

    ---

    One async block makes the whole flow async. No manual routing — it just works.

-   :material-robot:{ .lg .middle } **LLM-Native**

    ---

    Build flows from JSON at runtime. Generate OpenAI function-calling schemas from your flow manifests.

-   :material-layers:{ .lg .middle } **Composable**

    ---

    Nest `Block → Chain → Flow` freely. Each layer adds orchestration, retry, and failure handling.

</div>

---

## Install

```bash
pip install vibeblocks
```

---

## Quick Example

```python
from vibeblocks import Flow, block, ExecutionContext, execute_flow
from vibeblocks.policies.failure import FailureStrategy

@block(max_attempts=3, backoff="EXPONENTIAL")
def fetch_data(ctx: ExecutionContext) -> None:
    ctx.data["result"] = call_api()

@block(undo=lambda ctx: rollback(ctx.data))
def save_record(ctx: ExecutionContext) -> None:
    save_to_db(ctx.data)

flow = Flow(
    name="pipeline",
    blocks=[fetch_data, save_record],
    strategy=FailureStrategy.COMPENSATE,
)

outcome = execute_flow(flow, data={})
print(outcome.status)  # SUCCESS
```

---

[Get Started](01-introduction.md){ .md-button .md-button--primary }
[API Reference](07-quick-reference-api.md){ .md-button }
