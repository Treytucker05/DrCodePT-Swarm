"""Tests for QA agent."""

import pytest
from agent.autonomous.qa.qa_agent import QAAgent


def test_qa_agent_initialization():
    """Test QAAgent initialization."""
    qa = QAAgent()
    assert qa.checks_passed == 0
    assert qa.checks_failed == 0


def test_validate_result_valid():
    """Test validating a valid result."""
    qa = QAAgent()
    
    result = {
        "status": "success",
        "task_id": "task_1",
        "output": "test output",
    }
    
    report = qa.validate_result(result)
    assert report["valid"] is True
    assert report["score"] > 0


def test_validate_result_invalid():
    """Test validating an invalid result."""
    qa = QAAgent()
    
    result = {
        "status": "invalid_status",
        "task_id": "task_1",
    }
    
    report = qa.validate_result(result)
    assert report["valid"] is False
    assert len(report["issues"]) > 0


def test_validate_code_valid():
    """Test validating valid code."""
    qa = QAAgent()
    
    code = """
def hello():
    '''Say hello.'''
    return "hello"
"""
    
    report = qa.validate_code(code)
    assert report["valid"] is True


def test_validate_code_syntax_error():
    """Test validating code with syntax error."""
    qa = QAAgent()
    
    code = "def hello( return 'hi'"
    
    report = qa.validate_code(code)
    assert report["valid"] is False
    assert len(report["issues"]) > 0


def test_validate_code_dangerous_patterns():
    """Test detecting dangerous patterns."""
    qa = QAAgent()
    
    code = "eval('malicious code')"
    
    report = qa.validate_code(code)
    assert report["valid"] is False
    assert any("dangerous" in check.lower() for check in report["checks"])


def test_validate_research_with_sources():
    """Test validating research with sources."""
    qa = QAAgent()
    
    research = {
        "summary": "Test summary",
        "sources": [
            {"domain": "example.com", "url": "https://example.com/1"},
            {"domain": "other.com", "url": "https://other.com/1"},
        ],
    }
    
    report = qa.validate_research(research)
    assert report["valid"] is True


def test_validate_research_no_sources():
    """Test validating research without sources."""
    qa = QAAgent()
    
    research = {
        "summary": "Test summary",
        "sources": [],
    }
    
    report = qa.validate_research(research)
    assert report["valid"] is False


def test_qa_summary():
    """Test getting QA summary."""
    qa = QAAgent()
    
    # Simulate some checks
    qa.checks_passed = 10
    qa.checks_failed = 2
    
    summary = qa.get_summary()
    assert summary["total_checks"] == 12
    assert summary["pass_rate"] == pytest.approx(83.33, rel=0.01)
