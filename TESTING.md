# Testing & Verification

## Docker Build & Run

### Build from scratch
```bash
docker-compose build --no-cache
```

### Run service
```bash
docker-compose up -d
```

### Check container status
```bash
docker-compose ps
```

**Expected**: `contract-auditor` shows `Up` state

## Health Check

```bash
curl http://localhost:8080/health | jq
```

**Expected Output**:
```json
{
  "status": "healthy",
  "mode": "simulation",
  "medusa_available": true,
  "solc_available": true,
  "timestamp": "2026-01-16T12:00:00.000000"
}
```

## Audit Request

```bash
curl -X POST http://localhost:8080/audit \
  -F "file=@contracts/BrokenToken.sol" | jq
```

**Expected Output**:
```json
{
  "run_id": "20260116_120000",
  "status": "completed",
  "vulnerabilities_found": 5,
  "report_path": "/tmp/artifacts/20260116_120000/report.json",
  "sarif_path": null,
  "execution_time": 12.5,
  "mode": "simulation"
}
```

## Inspect Artifacts

```bash
docker exec contract-auditor ls -la /tmp/artifacts/<run_id>/
```

**Expected Files**:
- `report.json`
- `report.sarif.json` (if SARIF export enabled)

## View Logs

```bash
docker-compose logs auditor
```

**Expected**: 
- No `python3: can't open file '/app/python3'` errors
- JSON-formatted log lines (if structured logging enabled)
- Service starts successfully

## CLI Mode Test

```bash
docker run --rm contract-auditor
```

**Expected**: Runs audit in CLI mode (default command)

## Cleanup

```bash
docker-compose down -v
```

Removes containers and volumes.
