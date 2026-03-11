# **API Quick Reference**

This reference provides a condensed look at the primary classes and utilities within the VibeBlocks framework. All components are available via the top-level vibeblocks package.

## **1\. Core Executables**

### **Block**

Atomic unit of work wrapping a function.

* **Constructor:** Block(name, func, description=None, retry\_policy=None, undo=None, timeout=None)  
* **Properties:** is\_async: bool  
* **Methods:** execute(ctx) \-\> Outcome, compensate(ctx) \-\> None

### **Chain**

Linear sequence of executables.

* **Constructor:** Chain(name, blocks: List\[Executable\])  
* **Behavior:** Executes blocks sequentially. Fails if any step fails.

### **Flow**

Top-level orchestrator with error handling strategies.

* **Constructor:** Flow(name, blocks, description=None, strategy=FailureStrategy.ABORT)  
* **Methods:** get\_manifest() \-\> Dict (Used for AI/LLM integration).

## **2\. Execution State**

### **ExecutionContext\[T\]**

The central state container.

* **Attributes:**  
  * data: T: User-defined state object.  
  * trace: List\[Event\]: Chronological execution log.  
  * metadata: Dict: Custom key-value pairs.  
  * completed\_blocks: Set\[str\]: Internal set for tracking successful blocks.  
  * exception\_sanitizer: Callable\[\[Exception\], str\]: Hook to sanitize exception messages before they are written to the trace (default: str). Override in production to strip PII or secrets.  
* **Key Methods:**  
  * log\_event(level, source, message): Add entry to trace.  
  * format\_exception(e: Exception) \-\> str: Formats an exception using the configured sanitizer.  
  * to\_json() \-\> str: Serialize context to JSON.  
  * from\_json(raw, data\_cls=None): Restore context. Raises ValueError on invalid or malformed input. Supports Dataclasses and Pydantic.

## **3\. Decorators**

### **@block**

The primary entry point for defining tasks.

* **Arguments:**  
  * name, description: Identity and AI metadata.  
  * undo: Callable for compensation logic.  
  * timeout: Max execution time in seconds.  
  * **Retry Shortcut:** max\_attempts, delay, backoff, retry\_on, give\_up\_on.

@block(max\_attempts=3, backoff=BackoffStrategy.EXPONENTIAL)  
def my\_task(ctx: ExecutionContext):  
    ...

## **4\. Policies & Enums**

### **FailureStrategy (Flow Level)**

* ABORT: Stop immediately (Default).  
* CONTINUE: Log error and proceed.  
* COMPENSATE: Run undo handlers in reverse order.

### **BackoffStrategy (Retry Level)**

* FIXED: Constant delay.  
* LINEAR: delay \* attempt.  
* EXPONENTIAL: delay \* 2^(attempt-1).

### **RetryPolicy**

* **Fields:** max\_attempts, delay, backoff, max\_delay, jitter, retry\_on, give\_up\_on.  
* **Safety Limits:** max\_attempts is capped at MAX\_ATTEMPTS\_LIMIT (100); max\_delay is capped at MAX\_DELAY\_LIMIT (3600 s). Negative values are clamped to zero.

## **5\. Runtime & Execution Helpers**

### **execute\_flow**

High-level utility for rapid execution.

* **Signature:** execute\_flow(flow, data, async\_mode=False) \-\> Outcome

### **Runners**

* **SyncRunner.run(executable, ctx) \-\> Outcome**: For synchronous workloads. Raises RuntimeError on async blocks.  
* **AsyncRunner.run(executable, ctx) \-\> Awaitable\[Outcome\]**: For async or mixed workloads.

### **Outcome\[T\]**

The result object returned by runners.

* **Fields:** status (SUCCESS/FAILED/ABORTED), context, errors (List\[Exception\]), duration\_ms.

## **6\. Error Hierarchy**

All VibeBlocks exceptions extend a common base for targeted exception handling.

* **VibeBlocksError**: Base exception for all framework errors.  
  * **BlockExecutionError**: Raised when a Block fails permanently (after retries are exhausted).  
    * **BlockTimeoutError**: Raised when a Block exceeds its configured timeout.  
  * **ChainExecutionError**: Raised when a Chain detects an internal runtime invariant violation (e.g., an async step in a sync chain).

from vibeblocks.core.errors import BlockTimeoutError, BlockExecutionError

try:  
    outcome \= SyncRunner().run(flow, ctx)  
except BlockTimeoutError as e:  
    print(f"Step timed out: {e}")

## **7\. AI & Schema Utilities**

### **generate\_function\_schema**

Generates an OpenAI-compatible JSON Schema from a Flow manifest and an ExecutionContext data model. Located in vibeblocks.utils.schema.

* **Signature:** generate\_function\_schema(flow\_manifest: Dict, context\_model: Type) \-\> Dict  
* **Supports:** Pydantic v1/v2 models and standard Python Dataclasses.

from vibeblocks.utils.schema import generate\_function\_schema

tool\_schema \= generate\_function\_schema(flow.get\_manifest(), MyDataModel)

### **is\_async\_callable**

Determines if an object is an async callable. Located in vibeblocks.utils.inspection.

* **Signature:** is\_async\_callable(obj: Any) \-\> bool  
* **Detects:** async def functions, functools.partial wrappers around async functions, and objects with an async \_\_call\_\_ method.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*