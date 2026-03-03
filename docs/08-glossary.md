# **Glossary**

This glossary defines the core technical and architectural terms used within the VibeBlocks ecosystem. Consistent terminology is a cornerstone of the AA Digital Business engineering standard, ensuring clarity across complex AI-driven systems.

### **Atomic Unit**

The smallest, indivisible part of a workflow. in VibeBlocks, this is represented by a **Block**. An atomic unit should perform exactly one logical task and maintain its own retry and compensation logic.

### **Backoff Strategy**

An algorithm used to determine the delay between retry attempts after a transient failure. VibeBlocks supports:

* **Fixed:** Constant delay intervals.  
* **Linear:** Delay increases proportionally to the attempt count.  
* **Exponential:** Delay doubles with each attempt, effectively mitigating resource contention in distributed systems.

### **Block**

A "Leaf" executable that wraps a single Python function. It is the fundamental building block of any orchestration graph.

### **Chain**

A "Composite" executable that represents a linear, ordered sequence of steps. It handles sequential logic and bubbles up failures to the parent orchestrator.

### **Compensation (Undo Logic)**

A specialized function designed to revert the side effects of an operation. It is the core of the **Saga Pattern**, used by the COMPENSATE failure strategy to ensure system consistency after a downstream error.

### **Composite Pattern**

A structural design pattern that allows you to treat individual objects (Blocks) and compositions of objects (Chains or Flows) uniformly. In VibeBlocks, every component is an Executable.

### **Determinism**

The property where a system, given a specific starting state and input, will always produce the same output through the same execution path. VibeBlocks provides the deterministic "scaffolding" required to manage non-deterministic AI outputs.

### **ExecutionContext**

A serializable state container that flows through every step of a workflow. It acts as the "Single Source of Truth," housing business data, execution traces, and metadata.

### **Flow**

The top-level orchestrator. It manages a collection of executables and defines the global **Failure Strategy** for the entire process.

### **Idempotency**

The property of an operation where it can be applied multiple times without changing the result beyond the initial application. This is a critical requirement for robust **Compensation** logic and **Retries**.

### **Jitter**

The addition of a small amount of random noise to retry delays. This prevents "thundering herd" scenarios where multiple failed processes attempt to retry against a service at the exact same millisecond.

### **LIFO (Last-In-First-Out)**

The order in which compensation logic is executed. When a flow fails, VibeBlocks triggers undo handlers starting from the most recently successful step back to the first.

### **Outcome**

A data object returned by a Runner that summarizes the result of an execution. It contains the final status (SUCCESS, FAILED, or ABORTED), the updated ExecutionContext, and precise timing metrics.

### **Runner**

The execution engine responsible for evaluating the orchestration graph. VibeBlocks provides SyncRunner for blocking workloads and AsyncRunner for non-blocking, I/O-intensive AI workloads.

### **Semantic Layer**

The metadata layer (using the description field) that allows Large Language Models to understand the intent and requirements of a technical block without reading the underlying code.

### **Trace**

A chronological log of internal framework events captured within the ExecutionContext. Essential for auditing AI actions and debugging complex failure chains.

### **Zero-Gravity Philosophy**

An architectural commitment to keeping the framework lightweight and portable by avoiding mandatory external dependencies. This ensures that VibeBlocks can be integrated into any environment—from edge functions to enterprise cloud clusters—without bloating the system.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*