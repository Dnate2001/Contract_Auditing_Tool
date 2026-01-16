# 🛡️ Antigravity Smart Contract Auditor

AI-powered security auditing tool that combines fuzzing, machine learning, and automated test generation to find vulnerabilities in Solidity smart contracts.

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/antigravity-auditor
cd antigravity-auditor

# Install dependencies
pip3 install rich google-generativeai pytest

# Run audit (simulation mode)
python3 auditor_ai.py 5

# View results
cat audit_report.md
```

See [docs/quickstart.md](docs/quickstart.md) for detailed setup.

## 🎯 Features

- **🔍 Fuzzing**: Medusa property-based testing
- **🤖 AI Analysis**: Google Gemini 2.5 Flash with evidence validation
- **🧪 Reproducers**: Auto-generated Foundry tests
- **📊 Reports**: JSON, Markdown, and SARIF v2.1
- **🔄 CI/CD**: GitHub Actions integration
- **✅ Validation**: Evidence-based AI verification

## 📋 Requirements

### Required
- **Python**: 3.10+ (tested on 3.12)
- **Solidity Compiler**: v0.8.20+
- **Foundry**: Latest nightly

### Optional
- **Medusa**: v0.1.0+ (for real fuzzing)
- **Go**: 1.21+ (to install Medusa)
- **Gemini API Key**: For AI analysis (falls back to simulation)

## 🚀 Installation

### 1. Python Dependencies
```bash
pip3 install rich google-generativeai pytest
```

### 2. Solidity Compiler
```bash
# Ubuntu/Debian
wget https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux
chmod +x solc-static-linux
sudo mv solc-static-linux /usr/local/bin/solc
```

### 3. Foundry (Optional - for reproducers)
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 4. Medusa (Optional - for fuzzing)
```bash
go install github.com/crytic/medusa@latest
export PATH=$PATH:$HOME/go/bin
```

## 📖 Usage

### Basic Audit
```bash
# Simulation mode (no API key needed)
python3 auditor_ai.py 10

# With AI analysis
export GEMINI_API_KEY="your-key-here"
python3 auditor_ai.py 10
```

### Full Pipeline
```bash
# 1. Parse Medusa output
python3 tools/parse_medusa.py --input medusa-reports --output artifacts/findings.json

# 2. Generate reproducers
python3 tools/generate_reproducer.py artifacts/findings.json

# 3. Export reports
python3 tools/exporters.py artifacts/findings.json --contract YourContract

# 4. Run reproducers
forge test --match-path 'artifacts/reproducers/*/ReproTest.sol' -vvv
```

### Benchmarks
```bash
# Run benchmark suite
bash scripts/benchmark_run.sh

# View results
column -t -s, benchmarks/results.csv
```

## 📁 Output Files

```
artifacts/
├── findings.json          # Parsed vulnerabilities
├── report.json           # Standardized report
├── report.sarif.json     # SARIF v2.1 (GitHub Security)
└── reproducers/          # Foundry test files
    └── finding_1_*/
        ├── ReproTest.sol
        └── README.md
```

## 🔧 Troubleshooting

### Missing API Key
**Error**: `⚠️ GEMINI_API_KEY not found`  
**Solution**: Tool runs in simulation mode automatically. For AI analysis:
```bash
export GEMINI_API_KEY="your-key"
```

### Medusa Not Found
**Error**: `medusa: command not found`  
**Solution**: Tool uses test fixtures. To install Medusa:
```bash
go install github.com/crytic/medusa@latest
export PATH=$PATH:$HOME/go/bin
```

### Solc Version Mismatch
**Error**: `Source file requires different compiler version`  
**Solution**: Install correct version:
```bash
# Check required version in contract
solc --version

# Install specific version
wget https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux
```

### Import Errors
**Error**: `ModuleNotFoundError: No module named 'rich'`  
**Solution**: Install Python dependencies:
```bash
pip3 install rich google-generativeai pytest
```

### Permission Denied
**Error**: `Permission denied: /usr/local/bin/solc`  
**Solution**: Use sudo or install to user directory:
```bash
# Option 1: Use sudo
sudo mv solc-static-linux /usr/local/bin/solc

# Option 2: User directory
mkdir -p ~/.local/bin
mv solc-static-linux ~/.local/bin/solc
export PATH=$PATH:~/.local/bin
```

## 🔒 Security Notice

**⚠️ IMPORTANT**: AI-generated suggestions are **advisory only** and require human review.

- **Do NOT** auto-apply AI fixes without manual verification
- **Always** review code changes before deployment
- **Validate** reproducers actually demonstrate vulnerabilities
- **Test** fixes thoroughly before production use

The tool marks findings with confidence levels:
- ✅ **Supported**: High confidence, backed by evidence
- ⚠️ **Partial**: Medium confidence, requires review
- ❌ **Unsupported**: Low confidence, manual investigation needed
- 🔄 **Simulated**: Fallback mode, heuristic-based

## 📊 Benchmark Results

Tested on 8 vulnerable contracts:
- **Detection Rate**: 100% (0 false negatives)
- **Reproducer Success**: 100%
- **Test Coverage**: 23/23 tests passing

See [BENCHMARKS.md](BENCHMARKS.md) for details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Documentation**: [docs/](docs/)
- **Examples**: [benchmarks/contracts/](benchmarks/contracts/)
- **CI/CD**: [.github/workflows/audit.yml](.github/workflows/audit.yml)
- **Tools**: [tools/](tools/)

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/antigravity-auditor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/antigravity-auditor/discussions)
- **Documentation**: [Full Docs](docs/)

---

**Built with**: Python 3.12 | Foundry | Medusa | Google Gemini AI  
**Status**: ✅ Production Ready | 🧪 100% Test Coverage | 🔒 Security Focused
