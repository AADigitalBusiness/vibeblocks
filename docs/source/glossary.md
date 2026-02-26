# Glossary

- `ExecutionContext`: Mutable state container passed across steps.
- `Task`: Smallest executable unit; wraps a function.
- `Process`: Ordered sequence of executable steps.
- `Workflow`: Top-level executable that defines failure behavior.
- `RetryPolicy`: Rule set controlling retries on failure.
- `Compensation`: Undo logic executed after downstream failure.
- `Outcome`: Execution result with status and diagnostics.
- `Runner`: Engine that executes an executable graph.

