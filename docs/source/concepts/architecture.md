# Architecture

TaskChain uses a composite executable model:

- `Task` (leaf)
- `Process` (composite)
- `Workflow` (orchestrator)

State and traceability live in `ExecutionContext`.

Reference: [Core Concepts (full)](../core_concepts.md)

