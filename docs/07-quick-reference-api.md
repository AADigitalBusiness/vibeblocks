# **API Quick Reference**

This reference provides a condensed look at the primary classes and utilities within the VibeBlocks framework. All components are available via the top-level `vibeblocks` package.

---

## **1. Core Executables**

### **Block**
Atomic unit of work wrapping a function.

| Feature | Description |
| :--- | :--- |
| **Constructor** | `Block(name, func, description=None, retry_policy=None, undo=None, timeout=None)` |
| **Properties** | `is_async: bool` |
| **Methods** | `execute(ctx) -> Outcome`, `compensate(ctx) -> None` |

### **Chain**
Linear sequence of executables.

| Feature | Description |
| :--- | :--- |
| **Constructor** | `Chain(name, blocks: List[Executable])` |
| **Behavior** | Executes blocks sequentially. Fails if any step fails. |

### **Flow**
Top-level orchestrator with error handling strategies.

| Feature | Description |
| :--- | :--- |
| **Constructor** | `Flow(name, blocks, description=None, strategy=FailureStrategy.ABORT)` |
| **Methods** | `get_manifest() -> Dict` (Used for AI/LLM integration). |

---

## **2. Execution Context**

### **ExecutionContext[T]**
The central state container.

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `data` | `T` | User-defined state object. |
| `trace` | `List[Event]` | Chronological execution log. |
| `metadata` | `Dict` | Custom key-value pairs. |
| `completed_blocks` | `Set[str]` | Internal set for tracking successful blocks. |
| `exception_sanitizer` | `Callable` | Hook to sanitize exceptions (default: `str`). |

---

## **3. Decorators**

### **@block**
The primary entry point for defining tasks.

```python
@block(
    max_attempts=3, 
    backoff=BackoffStrategy.EXPONENTIAL,
    undo=my_rollback_func
)
def my_task(ctx: ExecutionContext):
    ...
```

**Arguments:**
- `name`, `description`: Identity and AI metadata.
- `undo`: Callable for compensation logic.
- `timeout`: Max execution time in seconds.
- **Retry Shortcut:** `max_attempts`, `delay`, `backoff`, `retry_on`, `give_up_on`.

---

## **4. Policies & Enums**

### **FailureStrategy (Flow Level)**
| Strategy | Description |
| :--- | :--- |
| `ABORT` | Stop immediately (Default). |
| `CONTINUE` | Log error and proceed. |
| `COMPENSATE` | Run undo handlers in reverse order. |

### **BackoffStrategy (Retry Level)**
| Strategy | Formula |
| :--- | :--- |
| `FIXED` | Constant delay. |
| `LINEAR` | `delay * attempt` |
| `EXPONENTIAL` | `delay * 2^(attempt-1)` |

---

## **5. Runtime & Output**

### **execute_flow**
High-level utility for rapid execution.

`execute_flow(flow, data, async_mode=False) -> Outcome`

### **Outcome[T]**
The result object returned by runners.

| Field | Description |
| :--- | :--- |
| `status` | `SUCCESS`, `FAILED`, or `ABORTED`. |
| `context` | The final `ExecutionContext`. |
| `errors` | `List[Exception]` encountered during run. |
| `duration_ms` | Execution time in milliseconds. |

---

## **6. AI & Schema Utilities**

### **generate_function_schema**
Generates an OpenAI-compatible JSON Schema from a Flow manifest.

```python
from vibeblocks.utils.schema import generate_function_schema
tool_schema = generate_function_schema(flow.get_manifest(), MyDataModel)
```

---

*Engineered with precision by AA Digital Business. High-end AI Architecture.*