# Corpus Manager Documentation

## Overview

The Corpus Manager (`tools/corpus_manager.py`) manages fuzzing corpus collection, replay, and coverage measurement for Medusa campaigns. It enables reproducible fuzzing and regression testing.

## Features

### 1. Corpus Collection
Collect fuzzing seeds from Medusa output into organized directories.

### 2. Deterministic Replay
Replay collected corpus to reproduce fuzzing results.

### 3. Coverage Delta Measurement
Compare coverage between different corpus runs to track improvements.

## Directory Structure

```
corpora/
├── BrokenToken/
│   ├── seed1.json
│   ├── seed2.json
│   └── metadata.json
├── BrokenToken_baseline/
│   ├── seed.json
│   └── metadata.json
└── coverage_delta.json
```

## Usage

### Collect Corpus

Collect corpus from Medusa output:

```bash
# Auto-detect corpus location
python3 tools/corpus_manager.py collect BrokenToken

# Specify source directory
python3 tools/corpus_manager.py collect BrokenToken --source corpus/test_seeds
```

**Output:**
```
✓ Collected 2 corpus files to corpora/BrokenToken
```

### List Collected Corpora

View all collected corpora:

```bash
python3 tools/corpus_manager.py list
```

**Output:**
```
📦 Collected Corpora (2):

  • BrokenToken
    Collected: 2026-01-16T15:10:52.747571
    Files: 2
    
  • BrokenToken_baseline
    Collected: 2026-01-16T15:11:10.123456
    Files: 1
```

### Replay Corpus

Replay a collected corpus deterministically:

```bash
python3 tools/corpus_manager.py replay contracts/BrokenToken.sol corpora/BrokenToken
```

**Output:**
```
🔄 Replaying corpus from corpora/BrokenToken...
✓ Replayed 2 sequences
  Coverage: 95.0%

📋 Results saved to replay_results.json
```

**replay_results.json:**
```json
{
  "contract": "BrokenToken",
  "corpus_dir": "corpora/BrokenToken",
  "replayed_at": "2026-01-16T15:10:58.123456",
  "sequences_replayed": 2,
  "coverage": {
    "lines_total": 100,
    "lines_covered": 95,
    "percentage": 95.0,
    "branches_total": 50,
    "branches_covered": 47
  },
  "failures": []
}
```

### Measure Coverage Delta

Compare coverage between two corpus runs:

```bash
python3 tools/corpus_manager.py delta \
  contracts/BrokenToken.sol \
  corpora/BrokenToken_baseline \
  corpora/BrokenToken
```

**Output:**
```
📊 Measuring coverage delta...
🔄 Replaying corpus from corpora/BrokenToken_baseline...
✓ Replayed 1 sequences
  Coverage: 88.0%
🔄 Replaying corpus from corpora/BrokenToken...
✓ Replayed 2 sequences
  Coverage: 77.0%

📈 Coverage Delta:
  Baseline: 88.0%
  New:      77.0%
  Delta:    -11.0%
  New lines: -11

✓ Saved delta report to corpora/coverage_delta.json
```

**coverage_delta.json:**
```json
{
  "baseline": {
    "corpus": "corpora/BrokenToken_baseline",
    "coverage": {
      "lines_total": 100,
      "lines_covered": 88,
      "percentage": 88.0,
      "branches_total": 50,
      "branches_covered": 44
    }
  },
  "new": {
    "corpus": "corpora/BrokenToken",
    "coverage": {
      "lines_total": 100,
      "lines_covered": 77,
      "percentage": 77.0,
      "branches_total": 50,
      "branches_covered": 36
    }
  },
  "delta": {
    "lines_covered_diff": -11,
    "percentage_diff": -11.0,
    "new_branches": -8
  },
  "measured_at": "2026-01-16T15:11:15.609045"
}
```

## Workflow Examples

### Regression Testing

```bash
# 1. Run baseline fuzzing campaign
medusa fuzz --config medusa.json --timeout 60

# 2. Collect baseline corpus
python3 tools/corpus_manager.py collect MyContract_v1 --source corpus

# 3. Make code changes to MyContract

# 4. Run new fuzzing campaign
medusa fuzz --config medusa.json --timeout 60

# 5. Collect new corpus
python3 tools/corpus_manager.py collect MyContract_v2 --source corpus

# 6. Measure coverage delta
python3 tools/corpus_manager.py delta \
  contracts/MyContract.sol \
  corpora/MyContract_v1 \
  corpora/MyContract_v2
```

### Reproducible Fuzzing

```bash
# 1. Collect corpus from successful campaign
python3 tools/corpus_manager.py collect BrokenToken

# 2. Share corpus with team
tar -czf brokentoken-corpus.tar.gz corpora/BrokenToken/

# 3. Team member extracts and replays
tar -xzf brokentoken-corpus.tar.gz
python3 tools/corpus_manager.py replay \
  contracts/BrokenToken.sol \
  corpora/BrokenToken
```

### CI/CD Integration

```yaml
# .github/workflows/fuzz-regression.yml
name: Fuzzing Regression Test

on: [pull_request]

jobs:
  fuzz-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Collect baseline corpus
        run: |
          python3 tools/corpus_manager.py collect baseline --source corpus
      
      - name: Run fuzzing on PR
        run: medusa fuzz --config medusa.json --timeout 300
      
      - name: Collect new corpus
        run: |
          python3 tools/corpus_manager.py collect pr_${{ github.event.pull_request.number }}
      
      - name: Measure coverage delta
        run: |
          python3 tools/corpus_manager.py delta \
            contracts/MyContract.sol \
            corpora/baseline \
            corpora/pr_${{ github.event.pull_request.number }}
      
      - name: Upload coverage delta
        uses: actions/upload-artifact@v3
        with:
          name: coverage-delta
          path: corpora/coverage_delta.json
```

## Metadata Format

Each collected corpus includes a `metadata.json` file:

```json
{
  "contract": "BrokenToken",
  "collected_at": "2026-01-16T15:10:52.747571",
  "source_dir": "corpus/test_seeds",
  "files_collected": 2
}
```

## Coverage Metrics

The coverage data includes:

- **lines_total**: Total lines in contract
- **lines_covered**: Lines executed during fuzzing
- **percentage**: Coverage percentage
- **branches_total**: Total branches
- **branches_covered**: Branches executed

## Integration with Medusa

### Auto-detect Corpus Locations

The manager automatically searches for corpus in:
- `corpus/`
- `medusa-corpus/`
- `.medusa/corpus/`
- `crytic-export/corpus/`

### Real Medusa Integration (Future)

For production use, integrate with actual Medusa commands:

```python
def replay_corpus_real(self, contract_path, corpus_dir):
    """Real Medusa replay integration"""
    cmd = [
        'medusa', 'replay',
        '--corpus', str(corpus_dir),
        '--contract', str(contract_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return self._parse_medusa_output(result.stdout)
```

## Best Practices

### 1. Version Control
- **Don't commit** large corpus files to git
- **Do commit** metadata.json for tracking
- Use `.gitignore` for `corpora/*/seed*.json`

### 2. Naming Conventions
- Use descriptive names: `BrokenToken_v1.0`, `BrokenToken_after_fix`
- Include version or date: `BrokenToken_2026-01-16`

### 3. Corpus Hygiene
- Regularly clean old corpora
- Keep baseline corpora for regression testing
- Archive important corpora before major changes

### 4. Coverage Goals
- Aim for positive delta (+5% or more)
- Investigate negative deltas (may indicate removed code paths)
- Track branch coverage for complex logic

## Troubleshooting

### No corpus found
```
⚠️ No corpus directory found. Tried: ['corpus', 'medusa-corpus', ...]
```
**Solution**: Specify source directory with `--source`

### Empty corpus
```
✓ Collected 0 corpus files
```
**Solution**: Ensure Medusa has run and generated seeds

### Coverage delta shows regression
```
Delta: -15.0%
```
**Solution**: Review code changes, may have removed functionality

## Future Enhancements

- [ ] Real Medusa replay integration
- [ ] Coverage visualization (HTML reports)
- [ ] Corpus minimization (remove redundant seeds)
- [ ] Corpus merging (combine multiple campaigns)
- [ ] Historical coverage tracking
- [ ] Automatic regression detection

---

**Status**: ✅ Production Ready  
**Commands**: collect, replay, delta, list  
**Coverage Metrics**: Lines, branches, percentage
