# **Core Concepts**

VibeBlocks is built upon a hierarchy of **Executable Units** and a centralized **State Container**. Understanding this hierarchy is essential for building scalable workflows that remain maintainable as business logic grows in complexity.

## **1\. The ExecutionContext: The Source of Truth**

The ExecutionContext\[T\] is the heart of every flow. It is a generic container that follows the "Single Source of Truth" principle.

* **Data (T):** Your business state. Whether it is a simple dictionary or a complex Pydantic model, this is the data your blocks mutate.  
* **Trace:** A chronological log of every event (starts, completions, errors, retries) within the execution.  
* **Metadata:** Global key-value pairs for infrastructure-level tracking (e.g., Request IDs).  
* **Serialization:** Every context is JSON-serializable out of the box, making it perfect for persisting long-running agents or debugging production failures.

## **2\. The Hierarchy of Executables**

VibeBlocks implements the **Composite Design Pattern**. Every component—from a single task to a complex multi-step process—is an Executable.

classDiagram  
    class Executable {  
        \<\<interface\>\>  
        \+execute(ctx)  
        \+compensate(ctx)  
        \+is\_async : bool  
    }  
    class Block {  
        \+func  
        \+undo  
        \+retry\_policy  
    }  
    class Chain {  
        \+blocks: List\[Executable\]  
    }  
    class Flow {  
        \+blocks: List\[Executable\]  
        \+strategy: FailureStrategy  
    }

    Executable \<|-- Block  
    Executable \<|-- Chain  
    Executable \<|-- Flow  
    Chain o-- Executable  
    Flow o-- Executable

### **Block (The Leaf)**

The Block is the atomic unit of work. It wraps a single Python function and enriches it with:

* **Semantic Metadata:** Descriptions that allow LLMs to understand the tool's purpose.  
* **Retry Policies:** Logic to handle transient failures automatically.  
* **Compensation Logic:** An optional "undo" function to revert side effects if the wider flow fails later.

### **Chain (The Composite)**

A Chain is an ordered sequence of Executables. It treats a group of blocks as a single logical unit. If any step in the chain fails, the chain fails immediately, bubbling the error up to the orchestrator.

### **Flow (The Orchestrator)**

The Flow is the top-level container. While a Chain focuses on sequence, a Flow focuses on **Orchestration Strategy**. It defines how the system should react when a step fails:

* **ABORT:** Stop everything immediately.  
* **CONTINUE:** Log the failure but press on (Best-effort).  
* **COMPENSATE:** The "Enterprise Grade" choice. Stop execution and run the undo logic for every previously successful step in reverse order.

## **3\. Determinism in an AI World**

VibeBlocks is designed to be the "Muscle" for an AI "Brain". By defining your tools as **Blocks** and your processes as **Flows**, you create a deterministic environment where:

1. **AI Plans:** The LLM decides which blocks to trigger or how to structure a dynamic flow.  
2. **VibeBlocks Executes:** The framework ensures that the state is managed, retries are handled, and failures are cleaned up properly.

This separation of concerns is what allows AA Digital Business to build AI agents that are safe for production environments.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*