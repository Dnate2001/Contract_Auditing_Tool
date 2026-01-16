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

---

## ngrok Demo Mode Verification

> [!WARNING]
> Demo mode exposes a public endpoint. Only use for temporary testing.

### Start Demo

```bash
# Configure .env first
cp .env.example .env
# Edit: set NGROK_AUTHTOKEN, DEMO_USER, DEMO_PASS

# Start demo (3-hour auto-shutdown)
bash scripts/start_ngrok_demo.sh
```

### Test Endpoints

```bash
# Health check (requires auth)
curl -u demo_user:your_password https://xxx.ngrok.io/health

# Audit request
curl -u demo_user:your_password \
  -X POST https://xxx.ngrok.io/audit \
  -F "file=@contracts/BrokenToken.sol"
```

### Verify Security

- [ ] Unauthenticated requests return 401
- [ ] Wrong credentials return 401
- [ ] CIDR restrictions work (if configured)
- [ ] Server auto-shuts down after 3 hours
- [ ] Artifacts isolated to `/tmp/artifacts_demo/`
- [ ] Warning banner displayed on startup

### Revoke Tunnel

```bash
# Kill processes
pkill -f ngrok
pkill -f demo_server

# Or use ngrok dashboard
# https://dashboard.ngrok.com/tunnels/agents
```

---

---

## ngrok Demo Mode Verification

> [!WARNING]
> Demo mode exposes a public endpoint. Only use for temporary testing.

### Start Demo

```bash
# Configure .env first
cp .env.example .env
# Edit: set NGROK_AUTHTOKEN, DEMO_USER, DEMO_PASS

# Start demo
bash scripts/start_ngrok_demo.sh
```

### Test Endpoints

```bash
# Health check (requires auth)
curl -u demo_user:change_me_strong_password https://xxx.ngrok.io/health

# Audit request
curl -u demo_user:change_me_strong_password \
  -X POST https://xxx.ngrok.io/audit \
  -F "file=@contracts/BrokenToken.sol"
```

### Verify Security

- [ ] Unauthenticated requests return 401
- [ ] Wrong credentials return 401
- [ ] CIDR restrictions work (if configured)
- [ ] Server auto-shuts down after TTL
- [ ] Artifacts isolated to `/tmp/artifacts_demo/`

### Revoke Tunnel

```bash
# Kill processes
pkill -f ngrok
pkill -f demo_server

# Or use ngrok dashboard
# https://dashboard.ngrok.com/tunnels/agents
```

---

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
