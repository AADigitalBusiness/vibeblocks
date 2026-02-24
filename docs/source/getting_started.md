<!-- @format -->

# Getting Started with TaskChain

## Installation

```bash
pip install taskchain
```

## Basic Usage: User Onboarding Example

This example demonstrates how to create a simple user onboarding workflow with compensation logic (rollback).

### 1. Define Execution Context

First, define the data structure that will hold your workflow's state.

```python
from dataclasses import dataclass
from taskchain.core.context import ExecutionContext

@dataclass
class UserData:
    email: str
    user_id: str | None = None
    status: str = "pending"

# Initialize Context
data = UserData(email="test@example.com")
ctx = ExecutionContext(data=data)

# You can serialize the context to JSON for storage
json_state = ctx.to_json()

# And deserialize it later, automatically parsing back the UserData class (or a Pydantic Model)
restored_ctx = ExecutionContext.from_json(json_state, data_cls=UserData)
```

### 2. Define Tasks

Create tasks using the `@task` decorator. Tasks can modify the context and define undo logic.

```python
from taskchain.core.decorators import task
from taskchain.policies.retry import RetryPolicy

@task()
def validate_email(ctx: ExecutionContext[UserData]):
    if "@" not in ctx.data.email:
        raise ValueError("Invalid email format")

def undo_create_account(ctx: ExecutionContext[UserData]):
    print(f"Rolling back account creation for {ctx.data.user_id}")
    ctx.data.user_id = None
    ctx.data.status = "deleted"

@task(undo=undo_create_account)
def create_account(ctx: ExecutionContext[UserData]):
    # Simulate DB call
    ctx.data.user_id = "user_123"
    ctx.data.status = "created"
    print("Account created")

@task(retry_policy=RetryPolicy(max_attempts=3))
def send_welcome_email(ctx: ExecutionContext[UserData]):
    print(f"Sending email to {ctx.data.email}")
    # Simulate potential failure
    # raise ConnectionError("SMTP Server down")
```

### 3. Orchestrate Workflow

Group tasks into a `Workflow` and execute it using a Runner.

```python
from taskchain.components.workflow import Workflow
from taskchain.policies.failure import FailureStrategy
from taskchain.runtime.runner import SyncRunner

# Define Workflow
# FailureStrategy.COMPENSATE will trigger undo logic if a step fails
workflow = Workflow(
    name="UserOnboarding",
    steps=[
        validate_email,
        create_account,
        send_welcome_email
    ],
    strategy=FailureStrategy.COMPENSATE
)

# Run Workflow
runner = SyncRunner()
outcome = runner.run(workflow, ctx)

if outcome.status == "SUCCESS":
    print(f"Workflow completed! User status: {ctx.data.status}")
else:
    print(f"Workflow failed: {outcome.errors}")
    print(f"Final status after compensation: {ctx.data.status}")
```

## Async Support

TaskChain supports async/await natively.

```python
import asyncio
from taskchain.runtime.runner import AsyncRunner

@task()
async def async_task(ctx):
    await asyncio.sleep(1)

async def main():
    outcome = await AsyncRunner().run(async_task, ctx)

# asyncio.run(main())
```
