# TaskChain

**TaskChain** is a lightweight, framework-agnostic Python library for organizing business logic using structured workflows. It focuses on Developer Experience (DX), type safety, and zero-gravity dependencies.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Zero-Gravity Core**: No mandatory external dependencies.
- **Type Safety**: Built with generics for full IDE support and static analysis (`mypy --strict`).
- **Composite Pattern**: Organize logic into `Task` -> `Process` -> `Workflow`.
- **Resilience**: Configurable retry policies with backoff and jitter.
- **Compensation**: Built-in support for undo/rollback logic (Saga pattern).
- **Traceability**: Complete execution history in a serializable `ExecutionContext`.
- **Hybrid Execution**: Supports both synchronous and asynchronous (`async`/`await`) execution.

## Installation

```bash
pip install taskchain
```

## Quick Start

```python
from dataclasses import dataclass
from taskchain import task, Workflow, ExecutionContext, FailureStrategy, SyncRunner

@dataclass
class UserData:
    email: str
    status: str = "pending"

@task
def validate_email(ctx: ExecutionContext[UserData]):
    if "@" not in ctx.data.email:
        raise ValueError("Invalid email")

@task(undo=lambda ctx: print("Rolling back user creation..."))
def create_user(ctx: ExecutionContext[UserData]):
    ctx.data.status = "created"
    print(f"User {ctx.data.email} created.")

# Organize tasks into a workflow
workflow = Workflow(
    name="Onboarding",
    steps=[validate_email, create_user],
    strategy=FailureStrategy.COMPENSATE
)

# Initialize context and run
ctx = ExecutionContext(UserData(email="test@example.com"))
outcome = SyncRunner().run(workflow, ctx)

print(f"Status: {outcome.status}")
```

## Documentation

Full documentation is available in the `docs/` directory. To build it locally:

```bash
pip install sphinx sphinx-rtd-theme myst-parser
cd docs
make html
```

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a pull request.

## License

MIT License
