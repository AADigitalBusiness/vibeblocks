# Core Concepts

TaskChain is built on a few core abstractions that separate business logic from orchestration.

## 1. ExecutionContext

The `ExecutionContext[T]` is the "single source of truth" for your workflow. It is a generic container that holds:

*   **Data (T)**: Your custom dataclass or dictionary (e.g., `UserData`).
*   **Trace**: A chronological log of `Event`s (start, end, error, retry).
*   **Metadata**: Arbitrary key-value pairs (e.g., execution ID, timestamps).

The context is passed to every task, allowing them to read and modify state *in-place*. It is designed to be fully serializable to JSON for debugging and persistence.

## 2. Executable Units

TaskChain uses a composite pattern where everything is an `Executable`:

### Task (Leaf)
The smallest unit of work. It wraps a Python function (sync or async) and adds:
*   **Retry Policy**: Configurable retries with backoff and jitter.
*   **Compensation**: Logic to undo changes if the workflow fails later.

### Process (Composite)
A linear sequence of tasks or sub-processes. It executes steps in order. If a step fails, the process fails and bubbles the error up.

### Workflow (Orchestrator)
The top-level container that defines the **Failure Strategy**:
*   **ABORT**: Stop immediately on error.
*   **CONTINUE**: Log error and proceed (best-effort).
*   **COMPENSATE**: Stop and run undo logic for all successful steps in reverse order (LIFO).

## 3. Runners

Runners handle the execution loop.

*   **SyncRunner**: Executes workflows synchronously. Raises an error if it encounters an async task.
*   **AsyncRunner**: Executes workflows asynchronously. Can handle both sync and async tasks transparently.

## 4. Zero-Gravity Philosophy

TaskChain intentionally avoids heavy dependencies. It does **not** include:
*   Database drivers
*   HTTP clients
*   Task queues (Celery/Redis)

It provides the structure; you provide the infrastructure. Services (like DB connections) should be injected into your tasks (e.g., via closure or class-based tasks) rather than carried in the serialized context.
