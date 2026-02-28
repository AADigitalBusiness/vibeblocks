# Contributing to VibeBlocks

Thank you for your interest in contributing to VibeBlocks.

## Getting Started

1. Clone the repository.
2. Install the package and development tools:
   ```bash
   pip install -e .[dev]
   ```
3. Run the test suite:
   ```bash
   python -m pytest tests/
   ```

## Project Layout

- Runtime code lives under `src/vibeblocks`.
- Tests live under `tests/`.
- Documentation sources live under `docs/source/`.

## Code Style

- Keep imports and examples aligned with the current package name: `vibeblocks`.
- Prefer small, focused changes with matching test coverage.
- Use type hints for public APIs and behavior-facing code.
- Run `ruff check .` and `ruff format .` when touching Python files.

## Submitting Changes

- Create a dedicated branch for each feature or fix.
- Keep pull requests scoped to a single logical change.
- Add or update tests when behavior changes.
- Update documentation when public APIs, examples, or terminology change.
- Submit a pull request with a clear title and a concise description of the change.

## Reporting Issues

Use the issue tracker to report bugs, regressions, or feature requests.
