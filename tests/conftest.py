"""Pytest fixtures for AI Governance Tool tests."""

import pytest
from pathlib import Path
from ai_governance.providers import ProviderFactory
from ai_governance.core.types import RefactorResult, TokenUsage, CostEstimate, ScanResult, Finding, SeverityLevel


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return "def foo(): pass"


@pytest.fixture
def sample_refactored_code():
    """Sample refactored Python code."""
    return "def foo() -> None: pass"


@pytest.fixture
def sample_refactor_result():
    """Sample successful refactor result."""
    return RefactorResult(
        success=True,
        refactored_code="def foo() -> None: pass",
        error=None,
        tokens_used=TokenUsage(input=100, output=50, total=150),
        cost=0.0015,
        model="claude-sonnet-4-5-20250929"
    )


@pytest.fixture
def sample_refactor_error():
    """Sample failed refactor result."""
    return RefactorResult(
        success=False,
        refactored_code=None,
        error="API error occurred",
        tokens_used=None,
        cost=0.0,
        model="claude-sonnet-4-5-20250929"
    )


@pytest.fixture
def sample_scan_result_allowed():
    """Sample scan result - file allowed."""
    return ScanResult(
        allowed=True,
        reason="No policy violations detected",
        findings=[],
        file_size=1024,
        error=False,
        content="def foo(): pass"
    )


@pytest.fixture
def sample_scan_result_blocked():
    """Sample scan result - file blocked."""
    finding = Finding(
        pattern="api_keys",
        description="API key detected",
        severity=SeverityLevel.CRITICAL,
        match_count=1,
        examples=["sk-1234..."]
    )
    return ScanResult(
        allowed=False,
        reason="Sensitive content detected - Critical: api_keys",
        findings=[finding],
        file_size=512,
        error=False,
        content="API_KEY = 'sk-1234567890'"
    )


@pytest.fixture
def provider_factory():
    """Provider factory instance."""
    return ProviderFactory()


@pytest.fixture
def temp_policy_file(tmp_path):
    """Create temporary policy file."""
    policy_content = """
name: "Test Policy"
version: "1.0"
description: "Test security policy"
blocked_file_patterns:
  - "**/secrets.yaml"
  - "**/.env"
sensitive_patterns:
  api_keys:
    pattern: "sk-[a-zA-Z0-9]{32,}"
    description: "API key detected"
    severity: "critical"
  passwords:
    pattern: "(?i)(password|passwd|pwd)\\s*=\\s*['\"][^'\"]{3,}['\"]"
    description: "Hardcoded password"
    severity: "high"
"""
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(policy_content)
    return str(policy_file)


@pytest.fixture
def temp_python_file(tmp_path):
    """Create temporary Python file."""
    py_file = tmp_path / "test.py"
    py_file.write_text("def hello():\n    return 'world'\n")
    return str(py_file)


@pytest.fixture
def temp_secrets_file(tmp_path):
    """Create temporary file with secrets."""
    secrets_file = tmp_path / "secrets.yaml"
    secrets_file.write_text("api_key: sk-abcdefghijklmnopqrstuvwxyz1234\n")
    return str(secrets_file)
