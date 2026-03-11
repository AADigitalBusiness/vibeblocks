# **Execution Runtime**

VibeBlocks provides a dual-engine architecture designed to handle both classic synchronous logic and modern asynchronous I/O (essential for AI API calls). This document details how to choose and configure the appropriate runner for your environment.

## **1\. Dual-Runner Architecture**

The framework abstracts execution through two primary classes: SyncRunner and AsyncRunner. These engines manage the orchestration lifecycle, including timing, tracing, and error propagation.

### **SyncRunner**

The SyncRunner is optimized for deterministic, CPU-bound tasks or legacy environments where asyncio is not present.

* **Behavior:** Executes blocks sequentially within the main thread.  
* **Safety Guard:** It performs a runtime check on every step. If a block returns a coroutine (indicating an async def function was used), the SyncRunner will raise a RuntimeError rather than allowing the task to fail silently.

### **AsyncRunner**

The AsyncRunner is the recommended choice for modern AI applications. It natively supports mixed workloads.

* **Behavior:** Uses a non-blocking event loop.  
* **Capability:** It can execute both synchronous def functions and asynchronous async def blocks. Synchronous functions are executed directly, while awaitables are awaited.

## **2\. Smart Async Detection**

VibeBlocks uses static inspection to build its execution tree. This is critical for maintaining "Zero-Gravity" performance without the overhead of heavy runtime wrappers.

from vibeblocks.utils.inspection import is\_async\_callable

\# VibeBlocks automatically identifies:  
\# 1\. async def functions  
\# 2\. functools.partial wrappers around async functions  
\# 3\. Objects with an async \_\_call\_\_ method

**Engineering Note:** While the framework is robust, it relies on standard Python definitions. Avoid patterns where a standard def function manually returns an awaitable (e.g., return asyncio.sleep(1)). This "sneaky" async behavior can bypass static detection and cause runtime failures in the SyncRunner.

## **3\. Timeout Management**

Reliability requires strict control over execution time. VibeBlocks implements timeouts differently depending on the runtime to ensure resource safety.

### **Synchronous Timeouts**

Synchronous blocks utilize a shared `ThreadPoolExecutor` (`_TASK_TIMEOUT_EXECUTOR`) that is reused across all timed blocks in the same process. This avoids the overhead of spawning new threads for each timeout and prevents thread leakage when many blocks run concurrently.

@block(timeout=2.0)  
def heavy\_computation(ctx):  
    \# If this takes \> 2s, a BlockTimeoutError is raised  
    ...

### **Asynchronous Timeouts**

Asynchronous blocks leverage asyncio.wait\_for, providing native, low-overhead cancellation of pending tasks without the need for additional threads.

## **4\. Performance Metrics**

Every execution outcome includes a duration\_ms field. This metric is calculated using high-resolution monotonic clocks (time.perf\_counter\_ns) to provide precise data for bottleneck analysis in complex AI pipelines.

outcome \= runner.run(flow, ctx)  
print(f"Total Latency: {outcome.duration\_ms}ms")

## **5\. Summary Table**

| Feature | SyncRunner | AsyncRunner |
| :---- | :---- | :---- |
| **Primary Use Case** | Local ETL / CPU tasks | Web APIs / LLM calls / Bots |
| **Mixed Blocks** | No (Raises Error) | Yes (Sync & Async) |
| **Timeout Mechanism** | ThreadPool (Managed) | Native asyncio.wait\_for |
| **Complexity** | Low | Medium (Requires Event Loop) |

*Engineered with precision by AA Digital Business. High-end AI Architecture.*