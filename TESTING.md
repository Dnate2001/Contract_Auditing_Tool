# TESTING & VERIFICATION (Manual & Docker)

This document lists commands to verify CLI and Docker behavior and parity with the auditor.

## Prerequisites

- Python 3.8+ and pip (for manual mode)
- Docker & docker-compose installed (for Docker mode)
- jq installed locally for JSON formatting (optional)
- Optional: Foundry/Hardhat for running reproducers locally

## Manual (Local) Test

```bash
# Setup venv and deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run auditor (example duration 60s)
python3 auditor_ai.py 60
```

## Docker Test (CLI in container)

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose run --rm contract-auditor python3 auditor_ai.py 60
```

## Inspect Artifacts

```bash
# Artifacts are written to data/artifacts/
ls -la data/artifacts

# Inspect compile.json and report
jq . data/artifacts/<job_id>/compile.json
jq . data/artifacts/<job_id>/report.json
```

## Handling Compile Warnings

The CLI pipeline persists compiler warnings in `artifacts/<job_id>/compile.json`.

Warnings should not cause the audit to exit with a fatal status when they are informational (for example: deprecation warnings such as `selfdestruct`).

## CLI Parity Test

Ensure behavior parity by running:

```bash
# Run auditor locally in container
docker run --rm -v $(pwd):/app -w /app contract-auditor python3 auditor_ai.py 10
```

Compare output to the manual run.

## Unit Tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Expected Behavior

### Successful Audit
- Exit code: 0
- Artifacts created in `data/artifacts/<run_id>/`
- Report files: `report.json`, `report.md`
- Compile warnings logged but not fatal

### Failed Audit
- Exit code: 1
- Error message displayed
- Partial artifacts may exist

## Troubleshooting

### Docker Issues
- Ensure Docker daemon is running
- Check `docker-compose ps` for container status
- View logs: `docker-compose logs auditor`

### Permission Errors
- Ensure `/data/artifacts` is writable
- Check user permissions in Dockerfile

### Missing Dependencies
- Verify all requirements installed: `pip list`
- Rebuild Docker image: `docker-compose build --no-cache`
