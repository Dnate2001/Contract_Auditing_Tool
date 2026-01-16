# Quickstart Guide

Get Smart Contract Auditor running in 5 minutes on a fresh Ubuntu 22.04 system.

## Prerequisites

- Ubuntu 22.04 (or similar Linux)
- Internet connection
- sudo access (for system-wide tools)

## Step-by-Step Installation

### 1. Update System
```bash
sudo apt update
sudo apt install -y wget curl git python3 python3-pip
```

### 2. Clone Repository
```bash
git clone https://github.com/Dnate2001/Contract_Auditing_Tool
cd Contract_Auditing_Tool
```

### 3. Install Python Dependencies
```bash
pip3 install rich google-generativeai pytest
```

### 4. Install Solidity Compiler
```bash
wget -q https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux
chmod +x solc-static-linux
sudo mv solc-static-linux /usr/local/bin/solc
solc --version
```

**Expected output**: `Version: 0.8.20+commit.a1b79de6.Linux.g++`

### 5. Verify Installation
```bash
python3 --version  # Should be 3.10+
solc --version     # Should be 0.8.20
```

## Running Your First Audit

### Option 1: Quick Demo (Simulation Mode)
```bash
# Run audit on sample contract (no API key needed)
python3 auditor_ai.py 5

# View results
cat audit_report.md
```

**Expected output**:
```
🔮 SMART CONTRACT AUDITOR
=====================
✓ Compiled BrokenToken.sol
✓ Found 5 vulnerabilities
✓ Generated AI analysis
✓ Saved report to audit_report.md
```

### Option 2: With AI Analysis
```bash
# Set API key
export GEMINI_API_KEY="your-gemini-api-key"

# Run audit
python3 auditor_ai.py 10

# View results
cat audit_report.md
```

### Option 3: Full Pipeline

#### Parse Medusa Output
```bash
python3 tools/parse_medusa.py \
  --input medusa-reports \
  --output artifacts/findings.json
```

#### Generate Reproducers
```bash
python3 tools/generate_reproducer.py artifacts/findings.json
```

#### Export Reports
```bash
python3 tools/exporters.py artifacts/findings.json --contract BrokenToken
```

#### View Reports
```bash
# JSON report
cat artifacts/report.json | python3 -m json.tool

# SARIF report
cat artifacts/report.sarif.json | python3 -m json.tool

# Markdown report
cat audit_report.md
```

## Testing the Installation

### Run Unit Tests
```bash
python3 -m pytest tests/ -v
```

**Expected**: All 23 tests pass

### Run Benchmarks
```bash
bash scripts/benchmark_run.sh
```

**Expected**: 8 contracts tested, 100% reproducer success

### Validate SARIF
```bash
python3 tools/validate_sarif.py artifacts/report.sarif.json
```

**Expected**: `✅ SARIF file is valid!`

## Docker Quickstart

For a completely isolated environment:

```dockerfile
# Dockerfile
FROM ubuntu:22.04

RUN apt update && apt install -y \
    wget curl git python3 python3-pip

WORKDIR /app
COPY . .

RUN pip3 install rich google-generativeai pytest

RUN wget -q https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux && \
    chmod +x solc-static-linux && \
    mv solc-static-linux /usr/local/bin/solc

CMD ["python3", "auditor_ai.py", "5"]
```

Build and run:
```bash
docker build -t contract-auditing-tool .
docker run contract-auditing-tool
```

## Verification Checklist

After installation, verify:

- [ ] Python 3.10+ installed
- [ ] `solc --version` shows v0.8.20
- [ ] `python3 auditor_ai.py 5` completes successfully
- [ ] `audit_report.md` generated
- [ ] Unit tests pass (`pytest tests/`)
- [ ] Benchmarks run (`bash scripts/benchmark_run.sh`)

## Next Steps

### 1. Audit Your Own Contract
```bash
# Copy your contract
cp /path/to/YourContract.sol contracts/

# Run audit
python3 auditor_ai.py 10

# Check results
cat audit_report.md
```

### 2. Generate Properties
```bash
python3 tools/generate_properties.py contracts/YourContract.sol
```

### 3. Set Up CI/CD
```bash
# Copy workflow
cp .github/workflows/audit.yml your-repo/.github/workflows/

# Add secret: GEMINI_API_KEY
# Push and create PR
```

## Troubleshooting

### Installation Fails
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Upgrade pip
pip3 install --upgrade pip

# Install with user flag
pip3 install --user rich google-generativeai pytest
```

### Solc Not Found
```bash
# Check PATH
echo $PATH

# Add to PATH
export PATH=$PATH:/usr/local/bin

# Verify
which solc
```

### Permission Issues
```bash
# Install to user directory
mkdir -p ~/.local/bin
wget -q https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux
chmod +x solc-static-linux
mv solc-static-linux ~/.local/bin/solc
export PATH=$PATH:~/.local/bin
```

## Common Errors

### `ModuleNotFoundError: No module named 'rich'`
**Solution**: `pip3 install rich`

### `solc: command not found`
**Solution**: Follow step 4 above

### `Permission denied: /usr/local/bin/solc`
**Solution**: Use `sudo mv` or install to `~/.local/bin`

### `GEMINI_API_KEY not found`
**Solution**: Tool runs in simulation mode automatically. For AI:
```bash
export GEMINI_API_KEY="your-key"
```

## Getting Help

- **Documentation**: [Full docs](../README.md)
- **Issues**: [GitHub Issues](https://github.com/Dnate2001/Contract_Auditing_Tool/issues)
- **Examples**: [Benchmark contracts](../benchmarks/contracts/)

---

**Estimated Time**: 5 minutes  
**Difficulty**: Beginner  
**Prerequisites**: Basic command line knowledge
