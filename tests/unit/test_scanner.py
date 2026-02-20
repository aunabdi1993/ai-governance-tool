"""Unit tests for Scanner."""

import pytest
from ai_governance.scanner import Scanner
from ai_governance.policy_engine import PolicyEngine
from ai_governance.core.types import ScanResult, SeverityLevel


def test_scanner_allows_clean_file(temp_python_file, temp_policy_file):
    """Test scanner allows clean Python file."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    result = scanner.scan_file(temp_python_file)

    assert isinstance(result, ScanResult)
    assert result.allowed is True
    assert result.error is False
    assert result.content is not None
    assert "hello" in result.content


def test_scanner_blocks_file_with_secrets(temp_secrets_file, temp_policy_file):
    """Test scanner blocks file with API keys."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    result = scanner.scan_file(temp_secrets_file)

    assert isinstance(result, ScanResult)
    assert result.allowed is False
    assert len(result.findings) > 0
    assert result.findings[0].severity == SeverityLevel.CRITICAL


def test_scanner_handles_nonexistent_file(temp_policy_file):
    """Test scanner handles nonexistent files."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    result = scanner.scan_file("nonexistent.py")

    assert isinstance(result, ScanResult)
    assert result.allowed is False
    assert result.error is True
    assert "not found" in result.reason.lower()


def test_scanner_handles_directory(tmp_path, temp_policy_file):
    """Test scanner handles directories (not files)."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    result = scanner.scan_file(str(tmp_path))

    assert isinstance(result, ScanResult)
    assert result.allowed is False
    assert result.error is True
    assert "not a file" in result.reason.lower()


def test_scanner_handles_binary_file(tmp_path, temp_policy_file):
    """Test scanner handles binary files."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    # Create binary file
    binary_file = tmp_path / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")

    result = scanner.scan_file(str(binary_file))

    assert isinstance(result, ScanResult)
    assert result.allowed is False
    assert result.error is True
    assert "binary" in result.reason.lower() or "text" in result.reason.lower()


def test_scanner_returns_file_size(temp_python_file, temp_policy_file):
    """Test scanner returns correct file size."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    result = scanner.scan_file(temp_python_file)

    assert result.file_size > 0


def test_scanner_format_scan_result_allowed(sample_scan_result_allowed, temp_policy_file):
    """Test scanner formats allowed scan result."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    formatted = scanner.format_scan_result(sample_scan_result_allowed, "test.py")

    assert "test.py" in formatted
    assert "ALLOWED" in formatted
    assert "1024 bytes" in formatted


def test_scanner_format_scan_result_blocked(sample_scan_result_blocked, temp_policy_file):
    """Test scanner formats blocked scan result."""
    engine = PolicyEngine(temp_policy_file)
    scanner = Scanner(engine)

    formatted = scanner.format_scan_result(sample_scan_result_blocked, "secrets.py")

    assert "secrets.py" in formatted
    assert "BLOCKED" in formatted
    assert "api_keys" in formatted
    assert "critical" in formatted.lower()
