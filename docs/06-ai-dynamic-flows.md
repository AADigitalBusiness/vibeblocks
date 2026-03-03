# **AI-First Orchestration**

VibeBlocks is engineered to be the deterministic execution layer for Large Language Models (LLMs). While traditional orchestrators rely on static code definitions, VibeBlocks allows AI agents to plan and execute complex workflows dynamically via structured JSON schemas.

## **1\. The Semantic Layer**

For an LLM to use a tool effectively, it must understand its purpose. VibeBlocks uses the description field in the @block decorator to expose this metadata.

@block(  
    name="query\_inventory",  
    description="Queries the warehouse database for stock levels of a specific SKU."  
)  
def query\_inventory(ctx: ExecutionContext\[WarehouseData\]):  
    \# Logic to query DB  
    ...

By inspecting these blocks, VibeBlocks generates a **Manifest**—a structured dictionary that acts as a "menu" for the AI.

flow \= Flow("InventoryCheck", \[query\_inventory, notify\_manager\])  
manifest \= flow.get\_manifest()  
\# {  
\#   "name": "InventoryCheck",  
\#   "steps": \[{"name": "query\_inventory", "description": "..."}, ...\]  
\# }

## **2\. JSON Schema Generation**

To enable **Function Calling** or **Structured Outputs**, you need a valid JSON Schema. VibeBlocks automates this by mapping your ExecutionContext data models (Dataclasses or Pydantic) to standard schemas.

from vibeblocks.utils.schema import generate\_function\_schema

\# Generates a schema compatible with OpenAI/Gemini tool definitions  
tool\_schema \= generate\_function\_schema(flow.get\_manifest(), WarehouseData)

## **3\. Dynamic Execution from AI Planning**

Once an LLM has "planned" a flow, it returns a JSON object. The VibeBlocks.run\_from\_json method parses this plan and executes it instantly, maintaining all retry and compensation logic.

### **The Dynamic Workflow**

sequenceDiagram  
    participant LLM as AI Agent (Planner)  
    participant VB as VibeBlocks (Executor)  
    participant S as System Tools

    LLM-\>\>LLM: Analyzes User Request  
    LLM-\>\>VB: Sends JSON Plan (steps, strategy)  
    Note over VB: Resolves blocks from Registry  
    VB-\>\>S: Executes Step 1  
    VB-\>\>S: Executes Step 2  
    VB-\>\>VB: Handles Errors/Compensations  
    VB-\>\>LLM: Returns Final Outcome

### **Implementation Example**

from vibeblocks.vibeblocks import VibeBlocks

\# 1\. Received from LLM  
ai\_plan \= {  
    "name": "RefundAndNotify",  
    "steps": \["process\_refund", "send\_confirmation"\],  
    "strategy": "COMPENSATE"  
}

\# 2\. Registry of safe, predefined blocks  
available\_blocks \= {  
    "process\_refund": refund\_block,  
    "send\_confirmation": email\_block  
}

\# 3\. Dynamic execution  
result \= VibeBlocks.run\_from\_json(  
    ai\_plan,   
    initial\_data=RefundData(amount=50.0),   
    available\_blocks=available\_blocks  
)

## **4\. Why VibeBlocks for AI?**

* **Reliability:** LLMs are non-deterministic; VibeBlocks ensures that if the AI plans a 5-step process and step 4 fails, the previous 3 are rolled back properly.  
* **Safety:** You decide exactly which blocks are in the available\_blocks registry, preventing "prompt injection" from executing arbitrary code.  
* **Traceability:** The ExecutionContext captures a complete trace of the AI's actions, which is essential for auditing and debugging autonomous agents.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*