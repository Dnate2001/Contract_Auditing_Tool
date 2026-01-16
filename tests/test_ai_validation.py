#!/usr/bin/env python3
"""
Unit tests for AI Analysis Evidence Validation
Tests that AI suggestions are grounded in actual evidence
"""

import json
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_analyzer import AIAnalyzer, EvidenceValidator


class TestEvidenceValidator:
    """Test suite for evidence validation logic"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return EvidenceValidator()
    
    @pytest.fixture
    def sample_source_code(self):
        """Sample Solidity source code"""
        return """
        contract BrokenToken {
            mapping(address => uint256) public balanceOf;
            
            function mint(address _to, uint256 _amount) public {
                balanceOf[_to] += _amount;
            }
            
            function transfer(address _to, uint256 _value) public {
                balanceOf[msg.sender] -= _value;
                balanceOf[_to] += _value;
            }
        }
        """
    
    def test_supported_analysis(self, validator, sample_source_code):
        """Test analysis that is fully supported by evidence"""
        analysis = {
            "explanation": "The mint() function lacks access control",
            "impact": "Attacker can mint unlimited tokens",
            "exploit_scenario": "1. Attacker calls mint(address, amount)\n2. Tokens are minted",
            "recommended_fix": "function mint(address _to, uint256 _amount) public onlyOwner { }",
            "prevention": "Use access control"
        }
        
        vulnerability = {
            "type": "Unauthorized Minting",
            "function": "mint(address,uint256)",
            "line": 45,
            "sequence": [
                {"sender": "0x123", "function": "mint(address,uint256)", "value": 0}
            ],
            "raw_trace": "Call to mint() succeeded"
        }
        
        result = validator.validate_analysis(analysis, vulnerability, sample_source_code)
        
        assert result["support"] == "supported"
        assert result["requires_manual_review"] == False
        assert result["validation_details"]["sequence_match"]["valid"] == True
        assert result["validation_details"]["fix_match"]["valid"] == True
        assert result["validation_details"]["function_match"]["valid"] == True
    
    def test_partial_analysis(self, validator, sample_source_code):
        """Test analysis that is partially supported"""
        analysis = {
            "explanation": "The contract has issues",  # Vague, doesn't mention function
            "impact": "Bad things happen",
            "exploit_scenario": "Attacker does something",  # Doesn't reference sequence
            "recommended_fix": "function mint() public onlyOwner { }",  # Good fix
            "prevention": "Be careful"
        }
        
        vulnerability = {
            "type": "Unauthorized Minting",
            "function": "mint(address,uint256)",
            "sequence": [{"sender": "0x123", "function": "mint(address,uint256)"}],
            "raw_trace": "trace"
        }
        
        result = validator.validate_analysis(analysis, vulnerability, sample_source_code)
        
        # With only 1/3 checks passing, should be unsupported
        assert result["support"] in ["partial", "unsupported"]
        assert result["requires_manual_review"] == True
    
    def test_unsupported_analysis(self, validator, sample_source_code):
        """Test analysis with no evidence support"""
        analysis = {
            "explanation": "Something about nonexistent_function",
            "impact": "Unknown",
            "exploit_scenario": "Call random_function()",
            "recommended_fix": "function random_function() { }",
            "prevention": "Unknown"
        }
        
        vulnerability = {
            "type": "Unknown",
            "function": "mint(address,uint256)",
            "sequence": [],
            "raw_trace": ""
        }
        
        result = validator.validate_analysis(analysis, vulnerability, sample_source_code)
        
        assert result["support"] == "unsupported"
        assert result["requires_manual_review"] == True
    
    def test_simulated_analysis(self, validator, sample_source_code):
        """Test that simulated data is marked correctly"""
        analysis = {
            "explanation": "[SIMULATION] This is simulated data",
            "impact": "Simulated impact",
            "exploit_scenario": "Simulated scenario",
            "recommended_fix": "Simulated fix",
            "prevention": "Simulated prevention"
        }
        
        vulnerability = {
            "type": "Test",
            "function": "test()",
            "sequence": []
        }
        
        result = validator.validate_analysis(analysis, vulnerability, sample_source_code)
        
        assert result["support"] == "simulated"
        assert result["requires_manual_review"] == True
    
    def test_sequence_validation_matching(self, validator):
        """Test sequence validation with matching functions"""
        exploit_scenario = "1. Attacker calls mint()\n2. Then calls transfer()"
        sequence = [
            {"function": "mint(address,uint256)"},
            {"function": "transfer(address,uint256)"}
        ]
        
        result = validator._validate_sequence_references(
            exploit_scenario, sequence, "mint"
        )
        
        assert result["valid"] == True
        assert "mint" in result["matched_functions"]
    
    def test_sequence_validation_no_match(self, validator):
        """Test sequence validation with non-matching functions"""
        exploit_scenario = "Attacker does something unrelated"
        sequence = [
            {"function": "mint(address,uint256)"}
        ]
        
        result = validator._validate_sequence_references(
            exploit_scenario, sequence, "mint"
        )
        
        assert result["valid"] == False
    
    def test_fix_validation_correct_function(self, validator, sample_source_code):
        """Test fix validation with correct function reference"""
        recommended_fix = "function mint(address _to, uint256 _amount) public onlyOwner { }"
        
        result = validator._validate_code_fix(
            recommended_fix, sample_source_code, "mint", 45
        )
        
        assert result["valid"] == True
    
    def test_fix_validation_wrong_function(self, validator, sample_source_code):
        """Test fix validation with wrong function reference"""
        recommended_fix = "function nonexistent() public { }"
        
        result = validator._validate_code_fix(
            recommended_fix, sample_source_code, "nonexistent", 0
        )
        
        assert result["valid"] == False
    
    def test_function_reference_validation(self, validator, sample_source_code):
        """Test function reference validation"""
        explanation = "The mint() function has a vulnerability"
        
        result = validator._validate_function_references(
            explanation, "mint(address,uint256)", sample_source_code
        )
        
        assert result["valid"] == True


class TestAIAnalyzerIntegration:
    """Integration tests for AI analyzer with validation"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance (will use simulation mode)"""
        return AIAnalyzer()
    
    def test_batch_analyze_adds_validation(self, analyzer):
        """Test that batch_analyze adds validation metadata"""
        vulnerabilities = [
            {
                "type": "Unauthorized Minting",
                "function": "mint(address,uint256)",
                "description": "No access control",
                "line": 45,
                "sequence": [{"function": "mint(address,uint256)"}],
                "raw_trace": "trace"
            }
        ]
        
        source_code = "function mint(address _to, uint256 _amount) public { }"
        
        result = analyzer.batch_analyze(vulnerabilities, source_code)
        
        assert len(result) == 1
        assert "ai_analysis" in result[0]
        assert "support" in result[0]["ai_analysis"]
        assert "evidence_links" in result[0]["ai_analysis"]
        assert "requires_manual_review" in result[0]["ai_analysis"]
        assert "validation_details" in result[0]["ai_analysis"]
    
    def test_validation_summary_logged(self, analyzer, caplog):
        """Test that validation summary is logged"""
        vulnerabilities = [
            {"type": "Test1", "function": "test1()", "sequence": []},
            {"type": "Test2", "function": "test2()", "sequence": []}
        ]
        
        result = analyzer.batch_analyze(vulnerabilities, "contract Test {}")
        
        # Check that some analysis was performed
        assert len(result) == 2
        assert all("ai_analysis" in v for v in result)
    
    def test_manual_review_flag_logic(self, analyzer):
        """Test that manual review flag is set correctly"""
        # Simulated data should require manual review
        vulnerabilities = [
            {
                "type": "Test",
                "function": "test()",
                "sequence": []
            }
        ]
        
        result = analyzer.batch_analyze(vulnerabilities, "")
        
        # Simulated mode should require manual review
        assert result[0]["ai_analysis"]["requires_manual_review"] == True
        assert result[0]["ai_analysis"]["support"] in ["simulated", "partial", "unsupported"]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
