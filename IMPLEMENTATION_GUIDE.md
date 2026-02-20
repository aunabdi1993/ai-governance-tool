# Implementation Guide for Completing the Refactoring

This guide provides step-by-step instructions for completing each remaining phase of the refactoring.

---

## Phase 3: Implement ABC Contracts

### Step 1: Update PolicyEngine

**File:** `ai_governance/policy_engine.py`

```python
# Add import at the top
from .core.base import GovernanceEngine
from .core.types import Finding, PolicyInfo, SeverityLevel

# Change class declaration
class PolicyEngine(GovernanceEngine):  # Add inheritance
    """YAML-based policy engine for security governance."""

    # Update method signatures to match ABC
    def is_file_blocked(self, filepath: str) -> tuple[bool, Optional[str]]:
        """Check if file path matches blocked patterns."""
        # Existing implementation stays the same
        pass

    def scan_content(self, content: str) -> List[Finding]:
        """Scan content for sensitive patterns."""
        # Convert existing implementation to return List[Finding]
        findings: List[Finding] = []
        for pattern_name, pattern_config in self.sensitive_patterns.items():
            matches = pattern_config['compiled'].findall(content)
            if matches:
                finding = Finding(
                    pattern=pattern_name,
                    description=pattern_config['description'],
                    severity=SeverityLevel(pattern_config['severity']),
                    match_count=len(matches),
                    examples=[m[:50] + '...' if len(m) > 50 else m for m in matches[:3]]
                )
                findings.append(finding)
        return findings

    def get_policy_info(self) -> PolicyInfo:
        """Get policy metadata."""
        return PolicyInfo(
            name=self.policy.get('name', 'Unknown'),
            version=self.policy.get('version', '1.0'),
            description=self.policy.get('description', ''),
            blocked_patterns_count=len(self.blocked_patterns),
            sensitive_patterns_count=len(self.sensitive_patterns),
        )
```

### Step 2: Update Scanner

**File:** `ai_governance/scanner.py`

```python
# Add import
from .core.base import SecurityScanner
from .core.types import ScanResult, Finding

# Change class declaration
class Scanner(SecurityScanner):  # Add inheritance
    """File security scanner."""

    # Update method to return ScanResult dataclass instead of dict
    def scan_file(self, filepath: str) -> ScanResult:
        """Scan a file for policy violations."""
        # Update existing implementation to use ScanResult
        try:
            # ... existing file reading logic ...

            # Instead of returning dict, return ScanResult
            return ScanResult(
                allowed=is_allowed,
                reason=reason,
                findings=findings,
                file_size=file_size,
                error=False,
                content=content if is_allowed else None
            )
        except Exception as e:
            return ScanResult(
                allowed=False,
                reason=str(e),
                findings=[],
                file_size=0,
                error=True,
                content=None
            )
```

**Update CLI to use ScanResult dataclass:**

```python
# In cli.py, change from:
scan_result = scanner.scan_file(filepath)
if scan_result['allowed']:
    content = scan_result['content']

# To:
scan_result = scanner.scan_file(filepath)
if scan_result.allowed:
    content = scan_result.content
```

### Step 3: Update AuditLogger

**File:** `ai_governance/audit_logger.py`

```python
# Add imports
from .core.base import BaseAuditLogger
from .core.types import AuditEntry, Finding, OperationStatus

# Change class declaration
class AuditLogger(BaseAuditLogger):  # Add inheritance
    """SQLite-based audit logger."""

    def log_action(
        self,
        filepath: str,
        action: str,
        status: str,
        reason: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0,
        findings: Optional[List[Finding]] = None,
        model: Optional[str] = None,
        target_description: Optional[str] = None,
        original_code: Optional[str] = None,
        refactored_code: Optional[str] = None,
        **kwargs: Any,
    ) -> int:
        """Log action to audit database."""
        # Existing implementation, ensure it returns record ID
        pass

    def get_recent_logs(self, limit: int = 50) -> List[AuditEntry]:
        """Get recent logs as AuditEntry objects."""
        # Convert existing dict-based returns to AuditEntry dataclasses
        rows = self._query_database("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return [self._row_to_audit_entry(row) for row in rows]

    def get_logs_by_status(self, status: str, limit: int = 50) -> List[AuditEntry]:
        """Get logs filtered by status."""
        rows = self._query_database(
            "SELECT * FROM audit_log WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
            (status, limit)
        )
        return [self._row_to_audit_entry(row) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics."""
        # Existing implementation stays the same
        pass

    def _row_to_audit_entry(self, row: tuple) -> AuditEntry:
        """Convert database row to AuditEntry."""
        return AuditEntry(
            id=row[0],
            timestamp=row[1],
            filepath=row[2],
            action=row[3],
            status=OperationStatus(row[4]),
            reason=row[5],
            tokens_used=row[6],
            cost=row[7],
            findings=json.loads(row[8]) if row[8] else [],
            model=row[9],
            target_description=row[10],
            original_code=row[11],
            refactored_code=row[12],
        )
```

### Step 4: Update ConfigManager

**File:** `ai_governance/config_manager.py`

```python
# Add imports
from .core.base import BaseConfigManager
from pathlib import Path

# Change class declaration
class ConfigManager(BaseConfigManager):  # Add inheritance
    """Multi-level configuration manager."""

    def find_config(self, explicit_path: Optional[str] = None) -> str:
        """Find configuration file."""
        # Existing implementation
        pass

    def init_project_config(self, template: str = "default-secure", force: bool = False) -> Path:
        """Initialize project-level config."""
        # Existing implementation, ensure it returns Path
        pass

    def init_user_config(self, template: str = "default-secure", force: bool = False) -> Path:
        """Initialize user-level config."""
        # Existing implementation, ensure it returns Path
        pass
```

---

## Phase 4: Add Type Hints

### Quick Checklist:
```bash
# Install mypy if not already
pip install mypy

# Run mypy to find issues
mypy ai_governance/

# Fix errors one by one
```

### Common Patterns:

```python
# Function signatures
def process_file(filepath: str, target: str, apply: bool = False) -> RefactorResult:
    pass

# Optional parameters
def get_config(path: Optional[str] = None) -> Dict[str, Any]:
    pass

# List/Dict types
def get_files(directory: str) -> List[Path]:
    pass

def get_metadata() -> Dict[str, Any]:
    pass

# Union types
def read_file(path: Union[str, Path]) -> str:
    pass

# Return None explicitly
def log_message(msg: str) -> None:
    print(msg)
```

---

## Phase 6: Create Test Suite

### Step 1: Create Test Structure

```bash
mkdir -p tests/unit tests/integration
touch tests/__init__.py
touch tests/conftest.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
```

### Step 2: Create Fixtures (tests/conftest.py)

```python
"""Pytest fixtures for AI Governance Tool tests."""

import pytest
from pathlib import Path
from ai_governance.providers import ProviderFactory, ClaudeProvider
from ai_governance.core.types import RefactorResult, TokenUsage, CostEstimate

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [{"text": "def foo() -> None: pass"}],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 50,
        }
    }

@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return "def foo(): pass"

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
def provider_factory():
    """Provider factory instance."""
    return ProviderFactory()

@pytest.fixture
def temp_policy_file(tmp_path):
    """Create temporary policy file."""
    policy_content = """
name: "Test Policy"
version: "1.0"
blocked_patterns:
  - "**/secrets.yaml"
sensitive_patterns:
  - pattern: "sk-[a-zA-Z0-9]{32}"
    description: "API key"
    severity: "critical"
"""
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(policy_content)
    return str(policy_file)
```

### Step 3: Create Unit Tests

**tests/unit/test_providers.py:**

```python
"""Unit tests for AI providers."""

import pytest
from ai_governance.providers import ProviderFactory, ClaudeProvider, OpenAIProvider
from ai_governance.core.exceptions import ConfigError, ProviderAuthError

def test_factory_creates_claude(provider_factory):
    """Test factory creates Claude provider."""
    provider = provider_factory.create("claude", api_key="test-key")
    assert isinstance(provider, ClaudeProvider)

def test_factory_creates_openai(provider_factory):
    """Test factory creates OpenAI provider."""
    provider = provider_factory.create("openai", api_key="test-key")
    assert isinstance(provider, OpenAIProvider)

def test_factory_unknown_provider(provider_factory):
    """Test factory raises error for unknown provider."""
    with pytest.raises(ConfigError, match="Unknown provider"):
        provider_factory.create("unknown")

def test_factory_lists_providers(provider_factory):
    """Test factory lists available providers."""
    providers = provider_factory.get_available_providers()
    assert "claude" in providers
    assert "openai" in providers

def test_claude_provider_requires_api_key():
    """Test Claude provider requires API key."""
    with pytest.raises(ProviderAuthError, match="API key"):
        ClaudeProvider(api_key=None)

def test_claude_provider_model_info():
    """Test Claude provider returns model info."""
    provider = ClaudeProvider(api_key="test-key")
    info = provider.get_model_info()
    assert info["provider"] == "claude"
    assert "model" in info
    assert "input_price_per_1m" in info
```

**tests/unit/test_policy_engine.py:**

```python
"""Unit tests for PolicyEngine."""

import pytest
from ai_governance.policy_engine import PolicyEngine
from ai_governance.core.types import Finding, SeverityLevel

def test_policy_engine_blocks_secrets_file(temp_policy_file):
    """Test policy engine blocks secrets files."""
    engine = PolicyEngine(temp_policy_file)
    is_blocked, reason = engine.is_file_blocked("config/secrets.yaml")
    assert is_blocked is True
    assert "secrets.yaml" in reason.lower()

def test_policy_engine_allows_normal_file(temp_policy_file):
    """Test policy engine allows normal files."""
    engine = PolicyEngine(temp_policy_file)
    is_blocked, reason = engine.is_file_blocked("src/main.py")
    assert is_blocked is False

def test_policy_engine_detects_api_key(temp_policy_file):
    """Test policy engine detects API keys."""
    engine = PolicyEngine(temp_policy_file)
    content = "API_KEY = 'sk-abcdefghijklmnopqrstuvwxyz1234'"
    findings = engine.scan_content(content)
    assert len(findings) > 0
    assert findings[0].severity == SeverityLevel.CRITICAL

def test_policy_engine_no_findings_clean_code(temp_policy_file):
    """Test policy engine finds nothing in clean code."""
    engine = PolicyEngine(temp_policy_file)
    content = "def hello(): print('world')"
    findings = engine.scan_content(content)
    assert len(findings) == 0
```

### Step 4: Create Integration Tests

**tests/integration/test_cli.py:**

```python
"""Integration tests for CLI commands."""

import pytest
from click.testing import CliRunner
from ai_governance.cli import cli

def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "AI Governance Tool" in result.output

def test_cli_config_command():
    """Test config command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['config'])
    assert result.exit_code == 0

# Add more integration tests for refactor, bulk-refactor, etc.
```

### Step 5: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ai_governance --cov-report=html

# Run specific test file
pytest tests/unit/test_providers.py -v

# Run specific test
pytest tests/unit/test_providers.py::test_factory_creates_claude -v
```

---

## Quick Wins

### 1. Format All Code (5 minutes)

```bash
make format
```

### 2. Run Linter (5 minutes)

```bash
make lint
# Fix any issues reported
```

### 3. Create Basic Tests (30 minutes)

Start with the easiest tests:
- Provider factory tests
- Exception tests
- Type validation tests

### 4. Add Type Hints to One Module (15 minutes)

Pick a small module and add complete type hints, then expand.

---

## Development Workflow

### Before Each Commit:

```bash
# 1. Format code
make format

# 2. Run linter
make lint

# 3. Run type checker
make typecheck

# 4. Run tests
make test

# Or run everything:
make quality
```

### For Pull Requests:

```bash
# 1. Run full quality check
make quality

# 2. Check coverage
pytest --cov=ai_governance --cov-report=term-missing

# 3. Ensure >80% coverage before merging
```

---

## Common Issues & Solutions

### Issue: Mypy errors about missing types

**Solution:** Add type stubs:
```bash
pip install types-PyYAML types-colorama types-requests
```

### Issue: Tests fail due to missing API key

**Solution:** Use mocks:
```python
@pytest.fixture
def mock_api_client(monkeypatch):
    def mock_create(*args, **kwargs):
        return MockResponse()
    monkeypatch.setattr('anthropic.Anthropic.messages.create', mock_create)
```

### Issue: Import errors in tests

**Solution:** Install package in editable mode:
```bash
pip install -e .
```

---

## Progress Tracking

Use GitHub Issues or a task board to track progress:

- [ ] Phase 3.1: PolicyEngine implements GovernanceEngine
- [ ] Phase 3.2: Scanner implements SecurityScanner
- [ ] Phase 3.3: AuditLogger implements BaseAuditLogger
- [ ] Phase 3.4: ConfigManager implements BaseConfigManager
- [ ] Phase 4: Add type hints to all modules
- [ ] Phase 6.1: Create test fixtures
- [ ] Phase 6.2: Unit tests for providers
- [ ] Phase 6.3: Unit tests for policy engine
- [ ] Phase 6.4: Unit tests for scanner
- [ ] Phase 6.5: Unit tests for audit logger
- [ ] Phase 6.6: Integration tests for CLI
- [ ] Phase 6.7: Achieve >80% coverage

---

## Questions?

Refer to:
- `REFACTORING_SUMMARY.md` - Overall plan and architecture
- `pyproject.toml` - Tool configurations
- `ai_governance/core/base.py` - Abstract base classes
- `ai_governance/core/types.py` - Type definitions
- `ai_governance/providers/claude.py` - Example provider implementation
