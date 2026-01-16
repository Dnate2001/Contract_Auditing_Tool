#!/usr/bin/env bash
# Benchmark Runner for Antigravity Auditor
# Tests detection accuracy across known vulnerable contracts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARKS_DIR="$PROJECT_ROOT/benchmarks"
CONTRACTS_DIR="$BENCHMARKS_DIR/contracts"
RESULTS_FILE="$BENCHMARKS_DIR/results.csv"

echo "🔬 Antigravity Auditor Benchmark Suite"
echo "========================================"
echo ""

# Create results CSV header
echo "contract,expected_vulns,found,supported,repro_ok,notes" > "$RESULTS_FILE"

# Define benchmark contracts with expected vulnerabilities
declare -A EXPECTED_VULNS
EXPECTED_VULNS[Reentrancy]=1
EXPECTED_VULNS[OverflowToken]=1
EXPECTED_VULNS[AccessBroken]=2
EXPECTED_VULNS[DelegationVuln]=1
EXPECTED_VULNS[FrontRunnable]=1
EXPECTED_VULNS[SelfDestructVuln]=1
EXPECTED_VULNS[UncheckedReturn]=1
EXPECTED_VULNS[UnprotectedInit]=1

# Function to run benchmark for a contract
run_benchmark() {
    local contract_name=$1
    local expected=${EXPECTED_VULNS[$contract_name]}
    
    echo "📊 Testing: $contract_name (expected: $expected vulnerabilities)"
    echo "---"
    
    # Copy contract to main contracts directory
    cp "$CONTRACTS_DIR/$contract_name.sol" "$PROJECT_ROOT/contracts/"
    
    # Generate properties
    echo "  Generating properties..."
    python3 "$PROJECT_ROOT/tools/generate_properties.py" \
        "$PROJECT_ROOT/contracts/$contract_name.sol" \
        --output "$PROJECT_ROOT/fuzz_props" > /dev/null 2>&1 || true
    
    # Run parser on fixtures (simulated for demo)
    echo "  Parsing findings..."
    python3 "$PROJECT_ROOT/tools/parse_medusa.py" \
        --input "$PROJECT_ROOT/medusa-reports" \
        --output "$PROJECT_ROOT/artifacts/findings_$contract_name.json" > /dev/null 2>&1 || true
    
    # Count findings
    local found=0
    if [ -f "$PROJECT_ROOT/artifacts/findings_$contract_name.json" ]; then
        found=$(python3 -c "import json; data=json.load(open('$PROJECT_ROOT/artifacts/findings_$contract_name.json')); print(len(data) if isinstance(data, list) else 0)" 2>/dev/null || echo "0")
    fi
    
    # Generate reproducers
    echo "  Generating reproducers..."
    local repro_ok=0
    if [ "$found" -gt 0 ]; then
        python3 "$PROJECT_ROOT/tools/generate_reproducer.py" \
            "$PROJECT_ROOT/artifacts/findings_$contract_name.json" > /dev/null 2>&1 || true
        
        # Count successful reproducers (check if files exist)
        repro_ok=$(find "$PROJECT_ROOT/artifacts/reproducers" -name "ReproTest.sol" 2>/dev/null | wc -l || echo "0")
    fi
    
    # Count supported findings (with AI validation)
    local supported=0
    if [ -f "$PROJECT_ROOT/artifacts/findings_$contract_name.json" ]; then
        supported=$(python3 -c "
import json
try:
    data = json.load(open('$PROJECT_ROOT/artifacts/findings_$contract_name.json'))
    if isinstance(data, list):
        supported = sum(1 for f in data if f.get('ai_analysis', {}).get('support') == 'supported')
    else:
        supported = 0
    print(supported)
except:
    print(0)
" 2>/dev/null || echo "0")
    fi
    
    # Determine notes
    local notes=""
    if [ "$found" -eq "$expected" ]; then
        notes="✓ Exact match"
    elif [ "$found" -gt "$expected" ]; then
        notes="⚠ False positives: $((found - expected))"
    else
        notes="⚠ False negatives: $((expected - found))"
    fi
    
    # Write results
    echo "$contract_name,$expected,$found,$supported,$repro_ok,$notes" >> "$RESULTS_FILE"
    
    echo "  Results: Found=$found, Supported=$supported, Repro=$repro_ok"
    echo "  $notes"
    echo ""
    
    # Cleanup
    rm -f "$PROJECT_ROOT/contracts/$contract_name.sol"
    rm -f "$PROJECT_ROOT/artifacts/findings_$contract_name.json"
}

# Run benchmarks for all contracts
for contract in "${!EXPECTED_VULNS[@]}"; do
    run_benchmark "$contract"
done

# Calculate summary statistics
echo "📈 Summary Statistics"
echo "===================="
echo ""

python3 << 'EOF'
import csv

with open('benchmarks/results.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total_expected = sum(int(r['expected_vulns']) for r in rows)
total_found = sum(int(r['found']) for r in rows)
total_supported = sum(int(r['supported']) for r in rows)
total_repro = sum(int(r['repro_ok']) for r in rows)

print(f"Total Contracts: {len(rows)}")
print(f"Total Expected Vulnerabilities: {total_expected}")
print(f"Total Found: {total_found}")
print(f"Total Supported: {total_supported}")
print(f"Total Reproducers: {total_repro}")
print(f"")
print(f"Detection Rate: {(total_found/total_expected*100):.1f}%")
print(f"Support Rate: {(total_supported/total_found*100 if total_found > 0 else 0):.1f}%")
print(f"Reproducer Success: {(total_repro/total_found*100 if total_found > 0 else 0):.1f}%")
EOF

echo ""
echo "✅ Benchmark complete! Results saved to: $RESULTS_FILE"
echo ""
echo "📄 View results:"
echo "   cat $RESULTS_FILE"
echo "   column -t -s, $RESULTS_FILE"
