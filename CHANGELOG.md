# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Docker restart loop caused by ENTRYPOINT/CMD duplication
- Permission errors on `/data/artifacts` and `/app/build` directories for non-root user
- Compilation warnings (e.g., `selfdestruct` deprecation) now treated as non-fatal
- CLI and Docker modes now have consistent behavior with exit codes
- Server.py error handling improved to match CLI behavior

### Changed
- Documentation updated to focus on CLI and Docker workflows only
- Removed HTTP service/FastAPI references from documentation
- Added comprehensive TESTING.md with verification steps
- Updated README with Docker & Manual Quickstart section

### Added
- Multi-stage Dockerfile with Medusa and solc
- Non-root user (auditor:auditor) in Docker container
- Build directory creation with proper permissions
- Graceful handling of compilation warnings
- Production readiness checklist

## [1.0.0] - 2026-01-16

### Added
- Initial release of Smart Contract Security Auditor
- Medusa fuzzing integration
- Google Gemini AI analysis
- Evidence validation system
- Professional report generation
- SARIF export support
- Vulnerability reproducer generation
