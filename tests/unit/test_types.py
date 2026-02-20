"""Unit tests for core type definitions."""

import pytest
from ai_governance.core.types import (
    Finding, ScanResult, TokenUsage, CostEstimate,
    RefactorResult, PolicyInfo, SeverityLevel
)


def test_finding_creation():
    """Test Finding dataclass creation."""
    finding = Finding(
        pattern="api_key",
        description="API key detected",
        severity=SeverityLevel.CRITICAL,
        match_count=1,
        examples=["sk-1234..."]
    )

    assert finding.pattern == "api_key"
    assert finding.severity == SeverityLevel.CRITICAL
    assert finding.match_count == 1


def test_finding_to_dict():
    """Test Finding converts to dict."""
    finding = Finding(
        pattern="api_key",
        description="API key detected",
        severity=SeverityLevel.CRITICAL,
        match_count=1,
        examples=["sk-1234..."]
    )

    d = finding.to_dict()
    assert d["pattern"] == "api_key"
    assert d["severity"] == "critical"
    assert isinstance(d, dict)


def test_scan_result_creation():
    """Test ScanResult dataclass creation."""
    result = ScanResult(
        allowed=True,
        reason="Clean file",
        findings=[],
        file_size=1024,
        error=False,
        content="code here"
    )

    assert result.allowed is True
    assert result.file_size == 1024
    assert result.content == "code here"


def test_token_usage_creation():
    """Test TokenUsage dataclass creation."""
    tokens = TokenUsage(input=100, output=50, total=150)

    assert tokens.input == 100
    assert tokens.output == 50
    assert tokens.total == 150


def test_cost_estimate_creation():
    """Test CostEstimate dataclass creation."""
    estimate = CostEstimate(
        estimated_input_tokens=100,
        estimated_output_tokens=50,
        estimated_total_tokens=150,
        estimated_cost=0.15
    )

    assert estimate.estimated_total_tokens == 150
    assert estimate.estimated_cost == 0.15


def test_refactor_result_success():
    """Test successful RefactorResult."""
    result = RefactorResult(
        success=True,
        refactored_code="def foo() -> None: pass",
        error=None,
        tokens_used=TokenUsage(100, 50, 150),
        cost=0.15,
        model="claude"
    )

    assert result.success is True
    assert result.refactored_code is not None
    assert result.error is None


def test_refactor_result_failure():
    """Test failed RefactorResult."""
    result = RefactorResult(
        success=False,
        refactored_code=None,
        error="API error",
        tokens_used=None,
        cost=0.0,
        model="claude"
    )

    assert result.success is False
    assert result.error is not None
    assert result.refactored_code is None


def test_policy_info_creation():
    """Test PolicyInfo dataclass creation."""
    info = PolicyInfo(
        name="Test Policy",
        version="1.0",
        description="Test description",
        blocked_patterns_count=5,
        sensitive_patterns_count=10
    )

    assert info.name == "Test Policy"
    assert info.blocked_patterns_count == 5


def test_severity_level_values():
    """Test SeverityLevel enum values."""
    assert SeverityLevel.CRITICAL.value == "critical"
    assert SeverityLevel.HIGH.value == "high"
    assert SeverityLevel.MEDIUM.value == "medium"
    assert SeverityLevel.LOW.value == "low"
