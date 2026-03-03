# **Contributor Guide**

Thank you for your interest in contributing to **VibeBlocks**. As the flagship open-source project of **AA Digital Business**, we maintain a high standard of engineering excellence. This guide outlines the technical requirements, architectural principles, and workflows required to contribute to the core library.

## **1\. Zero-Gravity Philosophy**

Every contribution must respect our core constraint: **No external dependencies.** VibeBlocks is designed to be a lightweight, "zero-gravity" framework. If you propose a feature that requires a third-party library (e.g., requests, pydantic, tenacity), it must be implemented as an optional integration or handled via protocol abstraction, ensuring the core package remains pure.

## **2\. Development Setup**

We use a modern Python stack with hatch for build management and pytest for testing.

### **Local Environment**

1. **Clone the repository:**  
   git clone \[https://github.com/AADigitalBusiness/vibeblocks.git\](https://github.com/AADigitalBusiness/vibeblocks.git)  
   cd vibeblocks

2. **Create a virtual environment and install in editable mode:**  
   python \-m venv .venv  
   source .venv/bin/activate  \# On Windows: .venv\\Scripts\\activate  
   pip install \-e .\[dev\]

## **3\. Architecture for Contributors**

Before writing code, understand the **Executable Interface**. Every new component must inherit from vibeblocks.core.executable.Executable and implement:

* is\_async (Property): Must correctly identify if the logic requires an event loop.  
* execute(ctx): The primary logic entry point.  
* compensate(ctx): The undo/rollback logic.

### **Static Inspection**

We rely on inspect.iscoroutinefunction for smart async detection. Ensure your components do not return "sneaky" awaitables from standard def methods, as this breaks the SyncRunner safety guards.

## **4\. Testing Standards**

We maintain a high test coverage. No pull request will be merged without matching tests.

* **Location:** All tests reside in the tests/ directory.  
* **Execution:** Run the suite using pytest.  
  python \-m pytest tests/

* **Requirements:** \* New features must include unit tests for both SyncRunner and AsyncRunner behavior.  
  * Failure scenarios (timeouts, retries) must be explicitly tested.

## **5\. Quality Gates (Linting & Typing)**

We use ruff for linting and formatting. Strict type hinting is mandatory for all public APIs.

\# Check formatting and linting  
ruff check .  
ruff format .

## **6\. Pull Request Workflow**

1. **Issue First:** Before a major change, open an issue to discuss the architectural impact with the AA Digital Business team.  
2. **Atomic Commits:** Use descriptive, atomic commit messages.  
3. **Documentation:** If you change a public API or add a block, you must update the relevant .md files in the documentation suite.  
4. **The "Flagship" Rule:** Ensure your code is clean, well-commented, and reflects the premium engineering standards of the studio.

*Engineered with precision by AA Digital Business. High-end AI Architecture.*