# AI Orchestration Guide

VibeBlocks is designed to be "AI-First". This means it exposes its internal structure in a way that Large Language Models (LLMs) can understand and manipulate.

## The Semantic Layer

### 1. Describing Blocks

Use the `description` parameter in the `@block` decorator to give context to the LLM.

```python
@block(description="Fetches user profile from the database using user_id.")
def fetch_user(ctx: ExecutionContext):
    ...
```

### 2. Getting the Manifest

The `Flow` object can generate a manifest that describes its structure.

```python
flow = Flow("UserOnboarding", [fetch_user, send_email])
manifest = flow.get_manifest()
# {
#   "name": "UserOnboarding",
#   "description": "...",
#   "steps": [
#     {"name": "fetch_user", "description": "Fetches user profile..."},
#     ...
#   ]
# }
```

## JSON Schema Generation

You can generate a JSON Schema for OpenAI Function Calling using `generate_function_schema`.

```python
from vibeblocks.utils.schema import generate_function_schema
from dataclasses import dataclass

@dataclass
class UserContext:
    user_id: int
    email: str

schema = generate_function_schema(flow.get_manifest(), UserContext)
```

Pass this schema to the LLM as a tool definition. The LLM will respond with a JSON object that `VibeBlocks.run_from_json` can execute.

## Dynamic Execution

Once you receive the JSON from the LLM:

```python
from vibeblocks.vibeblocks import VibeBlocks

llm_response = {
    "name": "GeneratedFlow",
    "steps": ["fetch_user", "validate_email", "send_email"],
    "strategy": "CONTINUE"
}

# Ensure you have a map of available blocks
available_blocks = {
    "fetch_user": fetch_user,
    "validate_email": validate_email,
    "send_email": send_email
}

result = VibeBlocks.run_from_json(llm_response, initial_data=UserContext(...), available_blocks=available_blocks)
```
