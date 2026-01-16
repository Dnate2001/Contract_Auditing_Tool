#!/usr/bin/env python3
"""
Unit tests for Medusa output parser
Tests defensive parsing, sequence extraction, and canonical format generation
"""

import json
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from parse_medusa import MedusaParser, parse_medusa_outputs


class TestMedusaParser:
    """Test suite for Medusa output parser"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs"""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def fixture_dir(self):
        """Path to test fixtures"""
        return Path(__file__).parent.parent / 'medusa-reports'
    
    def test_parse_fixture1_structured_json(self, fixture_dir):
        """Test parsing structured JSON with test_results array"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        # Should find at least 2 findings from fixture1.json
        assert len(findings) >= 2, f"Expected at least 2 findings, got {len(findings)}"
        
        # Check first finding (mint vulnerability)
        mint_finding = next((f for f in findings if 'mint' in f['function'].lower()), None)
        assert mint_finding is not None, "Should find mint vulnerability"
        assert mint_finding['type'] == 'Unauthorized Minting'
        assert mint_finding['contract'] == 'BrokenToken'
        assert mint_finding['severity'] == 'CRITICAL'
        assert 'sequence' in mint_finding
        assert len(mint_finding['sequence']) > 0
        
        # Verify sequence structure
        seq = mint_finding['sequence'][0]
        assert 'sender' in seq
        assert 'target' in seq
        assert 'function' in seq
        assert 'calldata' in seq
        assert 'value' in seq
    
    def test_parse_fixture2_newline_json(self, fixture_dir):
        """Test parsing newline-delimited JSON"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        # Should find delegatecall, randomness, and selfdestruct vulnerabilities
        vuln_types = {f['type'] for f in findings}
        
        assert 'Unrestricted Delegatecall' in vuln_types or 'Property Violation' in vuln_types
        assert any('random' in f['type'].lower() or 'random' in f['function'].lower() for f in findings)
        assert any('selfdestruct' in f['type'].lower() or 'destroy' in f['function'].lower() for f in findings)
    
    def test_canonical_fields_present(self, fixture_dir):
        """Test that all canonical fields are present in findings"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        required_fields = ['type', 'contract', 'function', 'line', 'description', 
                          'sequence', 'evidence_files', 'severity']
        
        for finding in findings:
            for field in required_fields:
                assert field in finding, f"Missing required field: {field}"
            
            # Verify sequence is a list
            assert isinstance(finding['sequence'], list), "sequence must be a list"
            
            # Verify evidence_files is a list
            assert isinstance(finding['evidence_files'], list), "evidence_files must be a list"
    
    def test_sequence_normalization(self, fixture_dir):
        """Test that call sequences are properly normalized"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        # Find a finding with a sequence
        finding_with_seq = next((f for f in findings if len(f['sequence']) > 0), None)
        assert finding_with_seq is not None, "Should have at least one finding with sequence"
        
        # Check sequence structure
        for call in finding_with_seq['sequence']:
            assert isinstance(call, dict), "Each call should be a dict"
            assert 'sender' in call
            assert 'function' in call
            # calldata, value, gas may be empty/0 but should exist
            assert 'calldata' in call
            assert 'value' in call
    
    def test_defensive_parsing_missing_keys(self, temp_dir):
        """Test parser handles missing keys gracefully"""
        # Create malformed JSON
        malformed = {
            "test_results": [
                {
                    "status": "failed"
                    # Missing most fields
                }
            ]
        }
        
        test_file = temp_dir / "malformed.json"
        with open(test_file, 'w') as f:
            json.dump(malformed, f)
        
        parser = MedusaParser(temp_dir)
        findings = parser.parse_medusa_outputs()
        
        # Should not crash, may extract partial data
        assert isinstance(findings, list)
    
    def test_defensive_parsing_corrupted_json(self, temp_dir):
        """Test parser handles corrupted JSON gracefully"""
        test_file = temp_dir / "corrupted.json"
        with open(test_file, 'w') as f:
            f.write('{"incomplete": "json"')  # Missing closing brace
        
        parser = MedusaParser(temp_dir)
        findings = parser.parse_medusa_outputs()
        
        # Should not crash
        assert isinstance(findings, list)
    
    def test_save_findings(self, fixture_dir, temp_dir):
        """Test saving findings to output file"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        output_file = temp_dir / "findings.json"
        parser.save_findings(output_file)
        
        assert output_file.exists()
        
        # Verify output is valid JSON
        with open(output_file) as f:
            loaded = json.load(f)
        
        assert isinstance(loaded, list)
        assert len(loaded) == len(findings)
    
    def test_public_api(self, fixture_dir):
        """Test public parse_medusa_outputs function"""
        findings = parse_medusa_outputs(str(fixture_dir))
        
        assert isinstance(findings, list)
        assert len(findings) > 0
        
        # Verify structure
        for finding in findings:
            assert 'type' in finding
            assert 'sequence' in finding
    
    def test_severity_inference(self, fixture_dir):
        """Test that severity levels are correctly inferred"""
        parser = MedusaParser(fixture_dir)
        findings = parser.parse_medusa_outputs()
        
        # Check that critical vulnerabilities are marked as such
        for finding in findings:
            if finding['type'] in ['Unauthorized Minting', 'Unrestricted Delegatecall', 
                                   'Unprotected Selfdestruct']:
                assert finding['severity'] == 'CRITICAL'
            
            # Severity should be one of the valid values
            assert finding['severity'] in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    
    def test_empty_directory(self, temp_dir):
        """Test parser handles empty directory gracefully"""
        parser = MedusaParser(temp_dir)
        findings = parser.parse_medusa_outputs()
        
        assert findings == []
    
    def test_nonexistent_directory(self):
        """Test parser handles nonexistent directory gracefully"""
        parser = MedusaParser(Path("/nonexistent/path"))
        findings = parser.parse_medusa_outputs()
        
        assert findings == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
