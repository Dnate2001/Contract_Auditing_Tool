# Deployment Guide

## Quick Start

### Option 1: Docker CLI Mode

```bash
# Build image
docker build -t contract-auditor:latest .

# Run audit (simulation mode)
docker run --rm \
  -v $(pwd)/contracts:/app/contracts:ro \
  -v $(pwd)/data:/data \
  contract-auditor:latest \
  auditor_ai.py 5

# Run audit (with AI)
docker run --rm \
  -e GEMINI_API_KEY="your-key" \
  -e MODE=production \
  -v $(pwd)/contracts:/app/contracts:ro \
  -v $(pwd)/data:/data \
  contract-auditor:latest \
  auditor_ai.py 30
```

### Option 2: Docker Compose Service Mode

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your GEMINI_API_KEY (optional)
nano .env

# 3. Start service
docker-compose up -d

# 4. Check health
curl http://localhost:8080/health

# 5. Submit audit
curl -X POST http://localhost:8080/audit \
  -F "file=@contracts/BrokenToken.sol"

# 6. View logs
docker-compose logs -f auditor

# 7. Stop service
docker-compose down
```

### Option 3: ngrok Exposure

```bash
# 1. Get ngrok auth token from https://dashboard.ngrok.com
export NGROK_AUTHTOKEN="your-token"

# 2. Start with ngrok profile
docker-compose --profile ngrok up -d

# 3. Get public URL
curl http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url'

# 4. Submit remote audit
curl -X POST https://xxx.ngrok.io/audit \
  -F "file=@contracts/BrokenToken.sol"
```

## Verification Steps

### 1. Docker Build

```bash
docker build -t contract-auditor:latest .
```

**Expected**:
- Build completes in < 5 minutes
- Image size < 500MB
- No errors or warnings

**Check**:
```bash
docker images contract-auditor:latest
# Should show image with size ~400-500MB
```

### 2. Health Check

```bash
docker-compose up -d
curl http://localhost:8080/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "mode": "simulation",
  "medusa_available": true,
  "solc_available": true,
  "timestamp": "2026-01-16T12:00:00Z"
}
```

### 3. Audit Request

```bash
curl -X POST http://localhost:8080/audit \
  -F "file=@contracts/BrokenToken.sol" \
  -o response.json

cat response.json | jq
```

**Expected Response**:
```json
{
  "run_id": "20260116_120000",
  "status": "completed",
  "vulnerabilities_found": 5,
  "report_path": "/data/artifacts/20260116_120000/report.json",
  "sarif_path": "/data/artifacts/20260116_120000/report.sarif.json",
  "execution_time": 12.5,
  "mode": "simulation"
}
```

### 4. Artifacts Check

```bash
ls -lh data/artifacts/*/
```

**Expected Files**:
- `report.json`
- `report.sarif.json`
- `reproducers/` directory

## Production Deployment

### AWS ECS

```bash
# 1. Build and push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker tag contract-auditor:latest <account>.dkr.ecr.us-east-1.amazonaws.com/contract-auditor:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/contract-auditor:latest

# 2. Create ECS task definition
# See docs/ecs-task-definition.json

# 3. Create ECS service
aws ecs create-service \
  --cluster production \
  --service-name contract-auditor \
  --task-definition contract-auditor:1 \
  --desired-count 2
```

### Google Cloud Run

```bash
# 1. Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/contract-auditor

# 2. Deploy
gcloud run deploy contract-auditor \
  --image gcr.io/PROJECT_ID/contract-auditor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MODE=simulation \
  --set-secrets GEMINI_API_KEY=gemini-key:latest \
  --memory 2Gi \
  --timeout 120s
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-auditor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contract-auditor
  template:
    metadata:
      labels:
        app: contract-auditor
    spec:
      containers:
      - name: auditor
        image: contract-auditor:latest
        ports:
        - containerPort: 8080
        env:
        - name: MODE
          value: "simulation"
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
        resources:
          limits:
            memory: "2Gi"
            cpu: "2000m"
          requests:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: auditor-data-pvc
```

## Monitoring

### Logs

```bash
# Docker Compose
docker-compose logs -f auditor

# Docker
docker logs -f contract-auditor

# Kubernetes
kubectl logs -f deployment/contract-auditor
```

### Metrics

```bash
# Container stats
docker stats contract-auditor

# Disk usage
du -sh data/artifacts/

# Request count
grep "POST /audit" data/logs/*.log | wc -l
```

### Alerts

Set up alerts for:
- Response time > 60s
- Error rate > 5%
- Disk usage > 80%
- Memory usage > 1.5GB

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs auditor

# Check health
docker-compose ps

# Restart
docker-compose restart auditor
```

### Out of Memory

```bash
# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G

# Restart
docker-compose up -d
```

### Slow Performance

```bash
# Check resource usage
docker stats

# Increase timeout
export MEDUSA_TIMEOUT=120

# Restart with new config
docker-compose up -d
```

## Security

### Secrets Management

**DO**:
- Use `.env` file (gitignored)
- Use Docker secrets
- Use cloud provider secret managers
- Rotate keys every 90 days

**DON'T**:
- Commit secrets to git
- Log secrets
- Include secrets in images
- Share secrets in plain text

### Network Security

```bash
# Run behind reverse proxy
docker run -p 127.0.0.1:8080:8080 contract-auditor

# Use TLS with nginx
# See docs/nginx.conf for example
```

## Backup & Recovery

### Backup Artifacts

```bash
# Daily backup
tar -czf backup-$(date +%Y%m%d).tar.gz data/artifacts/

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://backups/auditor/
```

### Restore

```bash
# Download backup
aws s3 cp s3://backups/auditor/backup-20260116.tar.gz .

# Extract
tar -xzf backup-20260116.tar.gz

# Restart service
docker-compose restart
```

## Performance Tuning

### Optimize Build

```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker build -t contract-auditor:latest .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t contract-auditor:latest .
```

### Optimize Runtime

```bash
# Use read-only filesystem
docker run --read-only --tmpfs /tmp contract-auditor

# Limit CPU
docker run --cpus="1.5" contract-auditor
```

---

**Last Updated**: 2026-01-16  
**Version**: 1.0.0
