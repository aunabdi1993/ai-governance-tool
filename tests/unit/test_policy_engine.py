"""Unit tests for PolicyEngine."""

import pytest
from ai_governance.policy_engine import PolicyEngine
from ai_governance.core.types import Finding, SeverityLevel, PolicyInfo


def test_policy_engine_loads_policy(temp_policy_file):
    """Test policy engine loads YAML policy file."""
    engine = PolicyEngine(temp_policy_file)
    assert engine.policy is not None
    assert engine.policy["name"] == "Test Policy"
    assert engine.policy["version"] == "1.0"


def test_policy_engine_blocks_secrets_file(temp_policy_file):
    """Test policy engine blocks secrets files."""
    engine = PolicyEngine(temp_policy_file)
    is_blocked, reason = engine.is_file_blocked("config/secrets.yaml")
    assert is_blocked is True
    assert "secrets.yaml" in reason


def test_policy_engine_blocks_env_file(temp_policy_file):
    """Test policy engine blocks .env files."""
    engine = PolicyEngine(temp_policy_file)
    is_blocked, reason = engine.is_file_blocked("project/.env")
    assert is_blocked is True
    assert ".env" in reason


def test_policy_engine_allows_normal_file(temp_policy_file):
    """Test policy engine allows normal files."""
    engine = PolicyEngine(temp_policy_file)
    is_blocked, reason = engine.is_file_blocked("src/main.py")
    assert is_blocked is False
    assert reason is None


def test_policy_engine_detects_api_key(temp_policy_file):
    """Test policy engine detects API keys."""
    engine = PolicyEngine(temp_policy_file)
    content = "API_KEY = 'sk-abcdefghijklmnopqrstuvwxyz1234'"
    findings = engine.scan_content(content)

    assert len(findings) > 0
    assert findings[0].pattern == "api_keys"
    assert findings[0].severity == SeverityLevel.CRITICAL
    assert findings[0].match_count == 1


def test_policy_engine_detects_password(temp_policy_file):
    """Test policy engine detects hardcoded passwords."""
    engine = PolicyEngine(temp_policy_file)
    content = 'password = "my_secret_password"'
    findings = engine.scan_content(content)

    assert len(findings) > 0
    password_finding = next((f for f in findings if f.pattern == "passwords"), None)
    assert password_finding is not None
    assert password_finding.severity == SeverityLevel.HIGH


def test_policy_engine_no_findings_clean_code(temp_policy_file):
    """Test policy engine finds nothing in clean code."""
    engine = PolicyEngine(temp_policy_file)
    content = "def hello():\n    return 'world'\n"
    findings = engine.scan_content(content)
    assert len(findings) == 0


def test_policy_engine_redacts_examples(temp_policy_file):
    """Test policy engine redacts sensitive examples."""
    engine = PolicyEngine(temp_policy_file)
    content = "API_KEY = 'sk-this_is_a_very_long_api_key_12345678901234567890'"
    findings = engine.scan_content(content)

    assert len(findings) > 0
    # Examples should be truncated
    for example in findings[0].examples:
        assert len(example) <= 13  # 10 chars + "..."


def test_policy_engine_get_policy_info(temp_policy_file):
    """Test policy engine returns policy metadata."""
    engine = PolicyEngine(temp_policy_file)
    info = engine.get_policy_info()

    assert isinstance(info, PolicyInfo)
    assert info.name == "Test Policy"
    assert info.version == "1.0"
    assert info.description == "Test security policy"
    assert info.blocked_patterns_count == 2
    assert info.sensitive_patterns_count == 2


def test_policy_engine_handles_missing_file():
    """Test policy engine raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        PolicyEngine("nonexistent.yaml")


def test_policy_engine_compiles_patterns(temp_policy_file):
    """Test policy engine compiles regex patterns."""
    engine = PolicyEngine(temp_policy_file)
    assert hasattr(engine, 'compiled_patterns')
    assert len(engine.compiled_patterns) > 0
    assert "api_keys" in engine.compiled_patterns
    assert "passwords" in engine.compiled_patterns
