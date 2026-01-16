# Pull Request

## Title
```
docs: Update documentation to CLI and Docker workflows only
```

## Description

This PR updates the repository documentation to focus exclusively on CLI and Docker usage, removing all references to FastAPI/HTTP service modes per project requirements.

### Changes Made

1. **README.md**
   - Replaced Quick Start section with "Docker & Manual Quickstart"
   - Removed service/API endpoint references
   - Added clear instructions for both local CLI and Docker CLI usage
   - Included troubleshooting notes for compilation warnings

2. **TESTING.md** (New)
   - Created comprehensive testing guide
   - Manual (local) test procedures
   - Docker test procedures
   - Artifact inspection commands
   - CLI parity verification
   - Unit test instructions

3. **CHANGELOG.md** (New)
   - Documented recent production fixes
   - Docker restart loop resolution
   - Permission error fixes
   - Compilation warning handling
   - CLI/Docker behavior consistency

4. **docs/FLOW.md**
   - Added paragraph explaining compilation warning behavior
   - Clarified that warnings are non-fatal and logged to artifacts
   - Documented CLI/Docker parity for exit codes

5. **. github/PULL_REQUEST_TEMPLATE.md** (New)
   - Added PR template with security checklist
   - Reminds contributors to check for secrets
   - Includes testing verification steps

### Testing

- ✅ All existing tests pass
- ✅ Documentation reviewed for service references (none found)
- ✅ No secrets or API keys committed
- ✅ Docker build verified
- ✅ CLI mode tested locally

### Breaking Changes

None. This is a documentation-only update.

### Checklist

- [x] No secrets or API keys committed
- [x] All tests pass
- [x] Docker build succeeds
- [x] CLI mode tested
- [x] Documentation updated
- [x] CHANGELOG.md updated

### Reviewer Notes

This PR removes all HTTP service/FastAPI documentation as requested. The project now documents only:
1. Manual (local) CLI usage
2. Docker containerized CLI usage

No functional code changes were made - this is purely documentation cleanup to match the project's intended usage model.
