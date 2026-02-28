# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-02-28

### Changed
- Updated the package metadata `Documentation` URL to point to the live docs site at `https://vibeblocks.aadigitalbusiness.com`.
- Added Wrangler configuration for deploying the Sphinx documentation to Cloudflare Workers assets.

## [0.1.0] - 2026-02-28

### Added
- Initial public deployment of VibeBlocks.
- Core components: `Block`, `Chain`, `Flow`, `ExecutionContext`.
- Resilience policies: `RetryPolicy`, `FailureStrategy`.
- Runtime runners: `SyncRunner`, `AsyncRunner`.
- Dynamic execution support through `VibeBlocks.run_from_json`.
- Documentation and initial project structure.
- `py.typed` marker for type checking support.
