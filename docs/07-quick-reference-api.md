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

* **Constructor:** Chain(name, steps: List\[Executable\])  
* **Behavior:** Executes steps sequentially. Fails if any step fails.

### **Flow**

Top-level orchestrator with error handling strategies.

* **Constructor:** Flow(name, steps, description=None, strategy=FailureStrategy.ABORT)  
* **Methods:** get\_manifest() \-\> Dict (Used for AI/LLM integration).

## **2\. Execution State**

### **ExecutionContext\[T\]**

The central state container.

* **Attributes:**  
  * data: T: User-defined state object.  
  * trace: List\[Event\]: Chronological execution log.  
  * metadata: Dict: Custom key-value pairs.  
  * completed\_steps: Set\[str\]: Internal set for tracking successful steps.  
* **Key Methods:**  
  * log\_event(level, source, message): Add entry to trace.  
  * to\_json() \-\> str: Serialize context to JSON.  
  * from\_json(raw, data\_cls=None): Restore context. Supports Dataclasses and Pydantic.

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

*Engineered with precision by AA Digital Business. High-end AI Architecture.*