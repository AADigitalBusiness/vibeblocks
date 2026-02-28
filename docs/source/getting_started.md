<!-- @format -->

# Getting Started with VibeBlocks

## Installation

```bash
pip install vibeblocks
```

## Basic Usage: User Onboarding Example

This example demonstrates how to create a simple user onboarding flow with compensation logic (rollback).

### 1. Define Execution Context

First, define the data structure that will hold your workflow's state.

```python
from dataclasses import dataclass
from vibeblocks import ExecutionContext

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

### 2. Define Blocks

Create blocks using the `@block` decorator. Blocks can modify the context and define undo logic.

```python
from vibeblocks import block
from vibeblocks.policies.retry import RetryPolicy

@block()
def validate_email(ctx: ExecutionContext[UserData]):
    if "@" not in ctx.data.email:
        raise ValueError("Invalid email format")

def undo_create_account(ctx: ExecutionContext[UserData]):
    print(f"Rolling back account creation for {ctx.data.user_id}")
    ctx.data.user_id = None
    ctx.data.status = "deleted"

@block(undo=undo_create_account)
def create_account(ctx: ExecutionContext[UserData]):
    # Simulate DB call
    ctx.data.user_id = "user_123"
    ctx.data.status = "created"
    print("Account created")

@block(retry_policy=RetryPolicy(max_attempts=3))
def send_welcome_email(ctx: ExecutionContext[UserData]):
    print(f"Sending email to {ctx.data.email}")
    # Simulate potential failure
    # raise ConnectionError("SMTP Server down")
```

### 3. Orchestrate a Flow

Group blocks into a `Flow` and execute it using a runner.

```python
from vibeblocks import Flow, SyncRunner
from vibeblocks.policies.failure import FailureStrategy

# Define Flow
# FailureStrategy.COMPENSATE will trigger undo logic if a step fails
flow = Flow(
    name="UserOnboardingFlow",
    steps=[
        validate_email,
        create_account,
        send_welcome_email
    ],
    strategy=FailureStrategy.COMPENSATE
)

# Run Workflow
runner = SyncRunner()
outcome = runner.run(flow, ctx)

if outcome.status == "SUCCESS":
    print(f"Flow completed! User status: {ctx.data.status}")
else:
    print(f"Flow failed: {outcome.errors}")
    print(f"Final status after compensation: {ctx.data.status}")
```

### 4. Grouping Blocks with Chain

You can group related blocks into a `Chain` to ensure they execute sequentially as a single unit. If any block in the chain fails, the entire chain fails.

```python
from vibeblocks import Chain

# Create a chain for account setup
account_setup_chain = Chain(
    name="AccountSetup",
    steps=[validate_email, create_account]
)

# Use the chain in the flow
flow = Flow(
    name="UserOnboardingFlow",
    steps=[
        account_setup_chain,
        send_welcome_email
    ],
    strategy=FailureStrategy.COMPENSATE
)
```

## Async Support

VibeBlocks supports async/await natively.

```python
import asyncio
from vibeblocks import AsyncRunner

@block()
async def async_block(ctx):
    await asyncio.sleep(1)

async def main():
    outcome = await AsyncRunner().run(async_block, ctx)

# asyncio.run(main())
```

## Simplified Execution

For simple use cases, you can use `execute_flow` to run a flow without manually creating the context and runner.

```python
from vibeblocks import execute_flow, Flow, block
from dataclasses import dataclass

@dataclass
class MyData:
    count: int

@block()
def increment(ctx):
    ctx.data.count += 1

# Define your flow
flow = Flow("SimpleFlow", [increment])

# Execute synchronously
# Automatically creates ExecutionContext(data=MyData(count=1)) and SyncRunner()
data = MyData(count=1)
outcome = execute_flow(flow, data)

print(f"Result: {outcome.context.data.count}") # Result: 2

# Execute asynchronously
# Automatically creates AsyncRunner()
# await execute_flow(flow, data, async_mode=True)
```
