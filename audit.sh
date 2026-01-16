#!/bin/bash
# Smart Contract Auditor - One-Command Setup and Execution
# This script handles all dependencies and runs the AI-powered auditing tool

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   AI-Powered Smart Contract Auditing Tool - Antigravity ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check Go installation
echo -e "${YELLOW}[1/5]${NC} Checking Go installation..."
if ! command -v go &> /dev/null; then
    echo -e "${RED}✗ Go is not installed. Please install Go 1.19+ first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Go $(go version | awk '{print $3}') detected${NC}"

# Step 2: Check Medusa
echo -e "${YELLOW}[2/5]${NC} Checking Medusa fuzzer..."
if [ ! -f "$HOME/go/bin/medusa" ]; then
    echo -e "${YELLOW}  Installing Medusa...${NC}"
    go install github.com/crytic/medusa@latest
fi
echo -e "${GREEN}✓ Medusa ready${NC}"

# Step 3: Check Solidity compiler
echo -e "${YELLOW}[3/5]${NC} Checking Solidity compiler..."
if [ ! -f "./bin/solc" ]; then
    echo -e "${YELLOW}  Downloading solc 0.8.20...${NC}"
    mkdir -p bin
    curl -sL https://github.com/ethereum/solidity/releases/download/v0.8.20/solc-static-linux -o bin/solc
    chmod +x bin/solc
fi
echo -e "${GREEN}✓ Solc 0.8.20 ready${NC}"

# Step 4: Compile contracts
echo -e "${YELLOW}[4/5]${NC} Compiling smart contracts..."
mkdir -p build
./bin/solc --bin --abi --optimize --overwrite \
    -o build \
    contracts/BrokenToken.sol test/BrokenToken.t.sol 2>&1 | grep -v "Warning:" || true
echo -e "${GREEN}✓ Contracts compiled${NC}"

# Step 5: Run Python auditor
echo -e "${YELLOW}[5/5]${NC} Launching AI Auditor..."
echo ""

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}  Creating Python virtual environment...${NC}"
    python3 -m venv venv 2>/dev/null || {
        echo -e "${YELLOW}  Using system Python (venv not available)${NC}"
        python3 auditor.py "$@"
        exit 0
    }
fi

# Activate venv and install dependencies
if [ -d "venv" ]; then
    source venv/bin/activate
    if [ ! -f "venv/.deps_installed" ]; then
        pip install -q rich requests
        touch venv/.deps_installed
    fi
    python auditor.py "$@"
else
    python3 auditor.py "$@"
fi
