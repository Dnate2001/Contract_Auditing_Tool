#!/usr/bin/env python3
"""
Unit tests for AI Analyzer with mocked Gemini client
Tests JSON parsing, fallback behavior, and support flag logic
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_analyzer import AIAnalyzer, EvidenceValidator


class TestEvidenceValidator:
    """Tests for evidence validation logic"""
    
    @pytest.fixture
    def validator(self):
        return EvidenceValidator()
    
    @pytest.fixture
    def sample_vulnerability(self):
        return {
            "type": "Unauthorized Minting",
            "function": "mint(address,uint256)",
            "line": 45,
            "sequence": [
                {"function": "mint(address,uint256)", "sender": "0x123"}
            ],
            "raw_trace": "Call to mint() succeeded"
        }
    
    @pytest.fixture
    def sample_source_code(self):
        return "function mint(address _to, uint256 _amount) public { }"
    
    def test_validate_supported_analysis(self, validator, sample_vulnerability, sample_source_code):
        """Test analysis that is fully supported by evidence"""
        analysis = {
            "explanation": "The mint() function lacks access control",
            "impact": "Critical vulnerability",
            "exploit_scenario": "1. Attacker calls mint(address, amount)",
            "recommended_fix": "function mint() public onlyOwner { }",
            "prevention": "Use access control"
        }
        
        result = validator.validate_analysis(analysis, sample_vulnerability, sample_source_code)
        
        assert result["support"] == "supported"
        assert result["requires_manual_review"] == False
        assert result["validation_details"]["function_match"]["valid"] == True
    
    def test_validate_partial_analysis(self, validator, sample_vulnerability, sample_source_code):
        """Test analysis with partial evidence support"""
        analysis = {
            "explanation": "There is a vulnerability",  # Vague
            "impact": "Bad",
            "exploit_scenario": "Attack happens",  # No sequence reference
            "recommended_fix": "function mint() public onlyOwner { }",  # Good
            "prevention": "Be careful"
        }
        
        result = validator.validate_analysis(analysis, sample_vulnerability, sample_source_code)
        
        assert result["support"] in ["partial", "unsupported"]
        assert result["requires_manual_review"] == True
    
    def test_validate_simulated_analysis(self, validator, sample_vulnerability, sample_source_code):
        """Test that simulated data is marked correctly"""
        analysis = {
            "explanation": "[SIMULATION] Simulated analysis",
            "impact": "Unknown",
            "exploit_scenario": "Unknown",
            "recommended_fix": "Unknown",
            "prevention": "Unknown"
        }
        
        result = validator.validate_analysis(analysis, sample_vulnerability, sample_source_code)
        
        assert result["support"] == "simulated"
        assert result["requires_manual_review"] == True


class TestAIAnalyzer:
    """Tests for AI Analyzer with mocked Gemini client"""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock google.generativeai module"""
        with patch('ai_analyzer.genai') as mock:
            yield mock
    
    @pytest.fixture
    def sample_vulnerability(self):
        return {
            "type": "Unauthorized Minting",
            "function": "mint(address,uint256)",
            "description": "Anyone can mint tokens",
            "line": 45,
            "sequence": [{"function": "mint(address,uint256)"}]
        }
    
    def test_initialization_with_api_key(self, mock_genai, monkeypatch):
        """Test analyzer initializes correctly with API key"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        analyzer = AIAnalyzer()
        
        assert analyzer.simulation_mode == False
        mock_genai.configure.assert_called_once_with(api_key="test-key")
    
    def test_initialization_without_api_key(self, mock_genai, monkeypatch):
        """Test analyzer falls back to simulation mode without API key"""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        analyzer = AIAnalyzer()
        
        assert analyzer.simulation_mode == True
    
    def test_json_parsing_success(self, mock_genai, monkeypatch):
        """Test successful JSON parsing from Gemini response"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "explanation": "Test explanation",
            "impact": "Test impact",
            "exploit_scenario": "Test scenario",
            "recommended_fix": "Test fix",
            "prevention": "Test prevention"
        })
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        result = analyzer._analyze_single({"type": "Test"}, "contract code")
        
        assert result["explanation"] == "Test explanation"
        assert result["impact"] == "Test impact"
    
    def test_json_parsing_with_markdown(self, mock_genai, monkeypatch):
        """Test JSON parsing strips markdown code blocks"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        # Mock Gemini response with markdown
        mock_response = Mock()
        mock_response.text = "```json\n" + json.dumps({
            "explanation": "Test",
            "impact": "Test",
            "exploit_scenario": "Test",
            "recommended_fix": "Test",
            "prevention": "Test"
        }) + "\n```"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        result = analyzer._analyze_single({"type": "Test"}, "code")
        
        assert result["explanation"] == "Test"
    
    def test_fallback_on_invalid_json(self, mock_genai, monkeypatch):
        """Test fallback to simulation when Gemini returns invalid JSON"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        # Mock Gemini response with invalid JSON
        mock_response = Mock()
        mock_response.text = "This is not JSON"
        
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        result = analyzer._analyze_single({"type": "Test"}, "code")
        
        # Should fall back to simulation
        assert "[FALLBACK]" in result["explanation"] or "[SIMULATION]" in result["explanation"]
    
    def test_batch_analyze_adds_validation(self, mock_genai, monkeypatch):
        """Test that batch_analyze adds validation metadata"""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        analyzer = AIAnalyzer()
        vulnerabilities = [{
            "type": "Unauthorized Minting",
            "function": "mint()",
            "sequence": []
        }]
        
        result = analyzer.batch_analyze(vulnerabilities, "contract code")
        
        assert len(result) == 1
        assert "ai_analysis" in result[0]
        assert "support" in result[0]["ai_analysis"]
        assert "requires_manual_review" in result[0]["ai_analysis"]
        assert "validation_details" in result[0]["ai_analysis"]
    
    def test_simulation_mode_fallback(self, monkeypatch):
        """Test simulation mode provides valid analysis"""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
        analyzer = AIAnalyzer()
        vulnerabilities = [{
            "type": "Unauthorized Minting",
            "function": "mint()",
            "description": "Test"
        }]
        
        result = analyzer.batch_analyze(vulnerabilities, "code")
        
        # Simulation data gets validated, may be partial/unsupported
        assert result[0]["ai_analysis"]["support"] in ["simulated", "partial", "unsupported"]
        assert result[0]["ai_analysis"]["requires_manual_review"] == True
        assert "explanation" in result[0]["ai_analysis"]
    
    def test_api_timeout_fallback(self, mock_genai, monkeypatch):
        """Test fallback when API times out"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        # Mock timeout exception
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Timeout")
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        vulnerabilities = [{"type": "Test", "function": "test()"}]
        
        result = analyzer.batch_analyze(vulnerabilities, "code")
        
        # Should fall back to simulation (may be validated as partial/unsupported)
        assert result[0]["ai_analysis"]["support"] in ["simulated", "partial", "unsupported"]
        assert result[0]["ai_analysis"]["requires_manual_review"] == True
    
    def test_retry_logic_success_on_second_attempt(self, mock_genai, monkeypatch):
        """Test retry logic succeeds on second attempt"""
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        # Mock first call fails, second succeeds
        mock_response = Mock()
        mock_response.text = json.dumps({
            "explanation": "Success",
            "impact": "Test",
            "exploit_scenario": "Test",
            "recommended_fix": "Test",
            "prevention": "Test"
        })
        
        mock_model = Mock()
        mock_model.generate_content.side_effect = [
            Exception("Temporary failure"),
            mock_response
        ]
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        result = analyzer._analyze_single({"type": "Test"}, "code")
        
        # Should succeed on retry
        assert result["explanation"] == "Success"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
