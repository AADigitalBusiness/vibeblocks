# **Getting Started**

This guide provides a practical walkthrough for setting up **VibeBlocks** and executing your first resilient workflow. Following the AA Digital engineering standards, we prioritize type safety and explicit state management from the very first line of code.

## **Installation**

VibeBlocks is a "Zero-Gravity" framework. It requires only a modern Python environment (3.8+).

pip install vibeblocks

## **Your First Workflow: Data Enrichment**

In this example, we will build a simple enrichment pipeline that validates an input and processes it.

### **1\. Define the Execution Context**

VibeBlocks flows revolve around a central ExecutionContext. We recommend using Python dataclasses or Pydantic models to define your state for full type-hinting support.

from dataclasses import dataclass  
from typing import Optional

@dataclass  
class ProcessingContext:  
    raw\_input: str  
    processed\_result: Optional\[str\] \= None  
    is\_valid: bool \= False

### **2\. Create Atomic Blocks**

Use the @block decorator to transform standard Python functions into managed units of work.

from vibeblocks import block, ExecutionContext

@block(description="Validates that the input string is not empty.")  
def validate\_input(ctx: ExecutionContext\[ProcessingContext\]):  
    if len(ctx.data.raw\_input) \> 0:  
        ctx.data.is\_valid \= True  
    else:  
        raise ValueError("Input cannot be empty")

@block(description="Transforms raw input into uppercase.")  
def transform\_data(ctx: ExecutionContext\[ProcessingContext\]):  
    ctx.data.processed\_result \= ctx.data.raw\_input.upper()

### **3\. Assemble and Execute**

For simple sequences, the execute\_flow utility provides a streamlined entry point that handles the initialization of the ExecutionContext and the SyncRunner.

from vibeblocks import Flow, execute\_flow

\# Define the orchestration structure  
pipeline \= Flow(  
    name="EnrichmentFlow",  
    steps=\[validate\_input, transform\_data\]  
)

\# Execute the flow with initial data  
initial\_state \= ProcessingContext(raw\_input="vibe\_blocks\_initial\_test")  
outcome \= execute\_flow(pipeline, initial\_state)

\# Inspect the result  
if outcome.status \== "SUCCESS":  
    print(f"Result: {outcome.context.data.processed\_result}")  
    print(f"Execution took: {outcome.duration\_ms}ms")  
else:  
    print(f"Flow failed with errors: {outcome.errors}")

## **Understanding the Execution Lifecycle**

When you run a flow, VibeBlocks performs several automated steps to ensure reliability:

sequenceDiagram  
    participant U as User Code  
    participant R as Runner  
    participant C as ExecutionContext  
    participant B as Block

    U-\>\>R: execute\_flow(Flow, Data)  
    R-\>\>C: Initialize(Data)  
    Note over R,C: Create Trace & Metrics  
    loop For each Step  
        R-\>\>B: execute(Context)  
        B-\>\>C: Log Event (Start)  
        B-\>\>B: Run User Logic  
        B-\>\>C: Update Data State  
        B-\>\>C: Log Event (Success)  
    end  
    R-\>\>U: Return Outcome Object

## **Next Steps**

Now that you have executed your first flow, you are ready to explore the core building blocks that allow for high-end AI orchestration:

* [**Core Concepts**](https://www.google.com/search?q=03-core-concepts.md)**:** Deep dive into Blocks, Chains, and Flows.  
* [**Failure Strategies**](https://www.google.com/search?q=06-failure-strategies-and-compensation.md)**:** Learn how to implement robust rollbacks and retries.  
* [**AI Integration**](https://www.google.com/search?q=07-ai-first-orchestration.md)**:** Connect your LLMs to VibeBlocks for dynamic tool execution.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*