<!-- @format -->

# Core Concepts

TaskChain is built on a few core abstractions that separate business logic from orchestration.

## 1. ExecutionContext

The `ExecutionContext[T]` is the "single source of truth" for your workflow. It is a generic container that holds:

- **Data (T)**: Your custom dataclass, Pydantic model or dictionary (e.g., `UserData`).
- **Trace**: A chronological log of `Event`s (start, end, error, retry).
- **Metadata**: Arbitrary key-value pairs (e.g., execution ID, timestamps).
- **Completed Steps**: A set (`completed_steps`) used internally for safely tracking executed steps during robust compensations.

The context is passed to every task, allowing them to read and modify state _in-place_. It is designed to be fully serializable to JSON for debugging and persistence. When deserializing via `from_json`, TaskChain automatically attempts to reconstruct strict types such as `dataclasses` or `Pydantic` models if you provide the class parameter.

## 2. Executable Units

TaskChain uses a composite pattern where everything is an `Executable`:

### Task (Leaf)

The smallest unit of work. It wraps a Python function (sync or async) and adds:

- **Retry Policy**: Configurable retries with backoff and jitter.
    - `max_attempts` (int): Total attempts before failure (default: 1).
    - `delay` (float): Base wait time in seconds (default: 1.0).
    - `backoff` (BackoffStrategy): Wait strategy (FIXED, LINEAR, EXPONENTIAL).
    - `retry_on` (List[Exception]): Exceptions that trigger a retry.
    - `give_up_on` (List[Exception]): Exceptions that immediately fail.
- **Compensation**: Logic to undo changes if the workflow fails later.

### Process (Composite)

A linear sequence of tasks or sub-processes. It executes steps in order. If a step fails, the process fails and bubbles the error up.

### Workflow (Orchestrator)

The top-level container that defines the **Failure Strategy**:

- **ABORT**: Stop immediately on error.
- **CONTINUE**: Log error and proceed (best-effort).
- **COMPENSATE**: Stop and run undo logic for all successful steps in reverse order (LIFO).

## 3. Runners

Runners handle the execution loop and are strict about async runtime evaluation:

- **SyncRunner**: Executes workflows synchronously. Raises a `RuntimeError` if it encounters an async task or an async compensation function that escaped static detection.
- **AsyncRunner**: Executes workflows asynchronously. Can handle both sync and async tasks transparently.

> **Warning:** TaskChain relies on static inspection (`inspect.iscoroutinefunction`) to build the execution tree. Always declare asynchronous user functions properly with `async def`. If a standard `def` function manually returns an awaitable (like returning `asyncio.sleep()`), the static parser will flag it as synchronous, potentially causing a `RuntimeError` at execution time in `SyncRunner`.

## 4. Zero-Gravity Philosophy

TaskChain intentionally avoids heavy dependencies. It does **not** include:

- Database drivers
- HTTP clients
- Task queues (Celery/Redis)

It provides the structure; you provide the infrastructure. Services (like DB connections) should be injected into your tasks (e.g., via closure or class-based tasks) rather than carried in the serialized context.
