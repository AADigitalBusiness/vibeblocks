# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-02-24

### Added
- Initial release of TaskChain.
- Core components: `Task`, `Process`, `Workflow`, `ExecutionContext`.
- Resilience policies: `RetryPolicy`, `FailureStrategy`.
- Runtime runners: `SyncRunner`, `AsyncRunner`.
- Documentation and examples.
- `py.typed` marker for type checking support.

### Fixed
- Serialization support for `set` and `Exception` types.
- Deserialization warnings for `ExecutionContext.from_json`.
- `Process` and `Workflow` now correctly return `Outcome` on exceptions instead of raising.
- `duration_ms` calculation in `Process` and `Workflow`.
- Decorator metadata preservation for `@task`.
- Runtime safety check for unawaited coroutines in sync execution (now properly closes them).
