# **Failure Strategies and Compensation**

In production-grade orchestration, "catching an error" is only the first step. True resilience requires a strategy for what happens next. VibeBlocks provides sophisticated failure management, including localized retries and global compensation (undo) logic.

## **1\. Local Resilience: Retry Policies**

Every Block can be configured with a RetryPolicy to handle transient errors (like network timeouts or temporary API rate limits) before the wider flow is even aware of a problem.

### **Configuration Options**

* **max\_attempts**: Total number of execution tries.  
* **backoff**: Strategy for wait times (FIXED, LINEAR, EXPONENTIAL).  
* **jitter**: Adds randomness to delays to prevent "thundering herd" issues in distributed systems.  
* **retry\_on / give\_up\_on**: Fine-grained control based on exception types.

from vibeblocks.policies.retry import RetryPolicy, BackoffStrategy

custom\_policy \= RetryPolicy(  
    max\_attempts=5,  
    delay=1.0,  
    backoff=BackoffStrategy.EXPONENTIAL,  
    jitter=True,  
    retry\_on=\[ConnectionError\] \# Only retry on connection issues  
)

@block(retry\_policy=custom\_policy)  
def unstable\_api\_call(ctx):  
    ...

## **2\. Global Resilience: Failure Strategies**

When a block fails permanently (exceeds retries), the Flow orchestrator decides the fate of the entire process based on its FailureStrategy.

| Strategy | Description | Best Use Case |
| :---- | :---- | :---- |
| ABORT | Stops execution immediately. | Critical data integrity where no undo is possible. |
| CONTINUE | Logs the error and moves to the next block. | Non-critical tasks (e.g., optional tracking). |
| COMPENSATE | Stops and triggers undo logic for all successful blocks. | Financial transactions or multi-step service updates. |

## **3\. The Compensation (Undo) Pattern**

The COMPENSATE strategy implements the **Saga Pattern**. If a step fails, VibeBlocks automatically executes the undo handlers of all *previously completed* blocks in reverse order (LIFO).

### **How it Works**

1. **Completion Tracking:** VibeBlocks maintains a completed\_blocks set in the ExecutionContext.  
2. **Reverse Trigger:** Upon failure, the orchestrator walks backward through the execution history.  
3. **Execution:** Only blocks that actually finished successfully have their undo functions called.

graph LR  
    subgraph Execution  
    A\[Step 1: OK\] \--\> B\[Step 2: OK\]  
    B \--\> C\[Step 3: FAIL\]  
    end  
      
    subgraph Compensation  
    C \-.-\> D\[Undo Step 2\]  
    D \-.-\> E\[Undo Step 1\]  
    end  
      
    style C fill:\#f96,stroke:\#333  
    style D fill:\#9cf,stroke:\#333  
    style E fill:\#9cf,stroke:\#333

### **Code Implementation**

def rollback\_db\_record(ctx):  
    print(f"Deleting record for user: {ctx.data.user\_id}")

@block(undo=rollback\_db\_record)  
def create\_db\_record(ctx):  
    \# Simulate database insertion  
    ctx.data.user\_id \= "uuid\_99"

@block()  
def trigger\_failure(ctx):  
    raise RuntimeError("Simulated downstream failure")

\# Setting the Flow to COMPENSATE ensures create\_db\_record is undone  
flow \= Flow("TransactionalFlow", \[create\_db\_record, trigger\_failure\], strategy=FailureStrategy.COMPENSATE)

## **4\. Engineering Best Practices**

* **Idempotency:** Ensure your undo functions are idempotent. If a compensation is retried or interrupted, running it again should not cause inconsistent state.  
* **Atomic State:** Use the ExecutionContext to store IDs or tokens generated during a block's execution so the undo function knows exactly what to revert.  
* **Async Compensation:** If your undo logic involves network calls (e.g., a DELETE request), define it as an async def. VibeBlocks will automatically await it if you are using the AsyncRunner.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*