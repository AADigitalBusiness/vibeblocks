# How to Choose SyncRunner vs AsyncRunner

## Rule of Thumb

- Use `SyncRunner` for synchronous task graphs.
- Use `AsyncRunner` when tasks or compensation handlers are asynchronous.

## Practical Notes

- Keep function signatures explicit (`def` vs `async def`).
- Avoid returning awaitables from non-async functions.

## Reference

See [Core Concepts](../core_concepts.md) for runtime behavior details.

