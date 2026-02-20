# Next Steps - Quick Start Guide

## What's Been Completed ✅

### Phase 1: Package Metadata & Configuration ✅
- Version unified to 1.0.0 (production-ready)
- Modern `pyproject.toml` with optional dependencies
- Pre-commit hooks configured
- Makefile with development commands
- Example configuration file (`.aigovern.yaml.example`)
- PEP 561 compliance (`py.typed` marker)

### Phase 2: Provider Architecture Migration ✅
- CLI migrated from `AIClient` to `ProviderFactory`
- `BatchProcessor` updated to use providers
- `CodebaseRefactor` updated to use providers
- Old `ai_client.py` deprecated (to be removed in Phase 11)

### Phase 9: Code Quality Tools ✅
- Black, Ruff, Mypy, Pytest configured
- Pre-commit hooks ready to use

### Phase 10: Documentation ✅
- `REFACTORING_SUMMARY.md` - Complete overview
- `IMPLEMENTATION_GUIDE.md` - Step-by-step instructions
- `docs/architecture.md` - Technical architecture
- `NEXT_STEPS.md` (this file)

---

## Priority: What to Do Next

### Option A: Complete MVP (Minimum Viable Production)

**Goal:** Get the tool production-ready ASAP

**Steps (4-6 hours):**

1. **Implement ABC Contracts (1 hour)**
   ```bash
   # Follow IMPLEMENTATION_GUIDE.md Phase 3
   # Update PolicyEngine, Scanner, AuditLogger, ConfigManager
   ```

2. **Add Basic Tests (2 hours)**
   ```bash
   # Follow IMPLEMENTATION_GUIDE.md Phase 6
   # Focus on high-value tests: providers, policy engine, scanner
   pytest tests/ --cov=ai_governance
   ```

3. **Add Type Hints to Critical Modules (1 hour)**
   ```bash
   # Focus on: cli.py, policy_engine.py, scanner.py
   mypy ai_governance/cli.py
   mypy ai_governance/policy_engine.py
   ```

4. **Clean Up (30 minutes)**
   ```bash
   # Delete ai_client.py
   # Remove setup.py
   make format
   make lint
   ```

5. **Validate (30 minutes)**
   ```bash
   make quality
   make build
   make check
   ```

### Option B: Full Production-Ready (Comprehensive)

**Goal:** Complete all refactoring phases

**Timeline:** 15-20 hours over 1-2 weeks

**Schedule:**

**Week 1:**
- Monday (2h): Phase 3 - Implement all ABC contracts
- Tuesday (2h): Phase 4 - Add type hints to all modules
- Wednesday (3h): Phase 6 - Create comprehensive test suite
- Thursday (2h): Phase 5 - Standardize return types
- Friday (1h): Phase 11 - Clean up legacy code

**Week 2:**
- Monday (2h): Phase 7 - Enhanced configuration system
- Tuesday (2h): Phase 8 - Improve error handling
- Wednesday (2h): More tests + documentation
- Thursday (1h): Phase 12 - Final validation
- Friday (1h): PyPI release

---

## Quick Commands

### Setup Development Environment

```bash
cd /Users/aunabdi/PycharmProjects/ai-governance-tool

# Install in dev mode with all extras
make install-dev

# Or manually:
pip install -e ".[dev,test,openai,dashboard]"
pre-commit install
```

### Run Quality Checks

```bash
# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run tests
make test

# Run everything
make quality
```

### Work on Phase 3 (ABC Contracts)

```bash
# 1. Edit PolicyEngine
code ai_governance/policy_engine.py
# Add: from .core.base import GovernanceEngine
# Change: class PolicyEngine(GovernanceEngine):

# 2. Edit Scanner
code ai_governance/scanner.py
# Add: from .core.base import SecurityScanner
# Change: class Scanner(SecurityScanner):
# Update return type of scan_file() to ScanResult

# 3. Edit AuditLogger
code ai_governance/audit_logger.py
# Add: from .core.base import BaseAuditLogger
# Change: class AuditLogger(BaseAuditLogger):

# 4. Edit ConfigManager
code ai_governance/config_manager.py
# Add: from .core.base import BaseConfigManager
# Change: class ConfigManager(BaseConfigManager):

# 5. Test
pytest tests/
```

### Work on Phase 6 (Tests)

```bash
# Create test structure
mkdir -p tests/unit tests/integration
touch tests/__init__.py tests/conftest.py

# Create first test file
cat > tests/unit/test_providers.py << 'EOF'
import pytest
from ai_governance.providers import ProviderFactory

def test_factory_creates_claude():
    factory = ProviderFactory()
    assert "claude" in factory.get_available_providers()
    assert "openai" in factory.get_available_providers()
EOF

# Run tests
pytest tests/ -v
```

---

## Common Tasks

### Add a New AI Provider

```bash
# 1. Create provider file
code ai_governance/providers/gemini.py

# 2. Implement AIProvider interface
# See IMPLEMENTATION_GUIDE.md for template

# 3. Register in factory
code ai_governance/providers/factory.py
# Add: from .gemini import GeminiProvider
# Add: self.register("gemini", GeminiProvider)

# 4. Test
pytest tests/unit/test_providers.py
```

### Add a New Security Pattern

```bash
# Edit policy file
code ai_governance/profiles/default-secure.yaml

# Add pattern:
# sensitive_patterns:
#   - pattern: 'your_regex_here'
#     description: 'What it detects'
#     severity: 'critical'  # or high, medium, low
```

### Check Test Coverage

```bash
pytest --cov=ai_governance --cov-report=html
open htmlcov/index.html
```

---

## Troubleshooting

### Import Errors

```bash
# Reinstall in editable mode
pip install -e .
```

### Mypy Errors

```bash
# Install type stubs
pip install types-PyYAML types-colorama types-requests

# Check specific file
mypy ai_governance/cli.py
```

### Tests Failing

```bash
# Run in verbose mode
pytest tests/ -v -s

# Run specific test
pytest tests/unit/test_providers.py::test_factory_creates_claude -v
```

### Pre-commit Fails

```bash
# Run manually to see errors
pre-commit run --all-files

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

---

## Progress Tracking

Use this checklist to track your progress:

### Phase 3: ABC Contracts
- [ ] PolicyEngine implements GovernanceEngine
- [ ] Scanner implements SecurityScanner
- [ ] AuditLogger implements BaseAuditLogger
- [ ] ConfigManager implements BaseConfigManager
- [ ] Update CLI to use ScanResult dataclass

### Phase 4: Type Hints
- [ ] Add type hints to cli.py
- [ ] Add type hints to policy_engine.py
- [ ] Add type hints to scanner.py
- [ ] Add type hints to all other modules
- [ ] Pass `mypy ai_governance/` with no errors

### Phase 5: Standardize Returns
- [ ] Scanner returns ScanResult (not dict)
- [ ] Update all callers to use dataclass attributes
- [ ] Remove dict access patterns

### Phase 6: Test Suite
- [ ] Create tests/conftest.py with fixtures
- [ ] Unit tests for providers (>80% coverage)
- [ ] Unit tests for policy_engine
- [ ] Unit tests for scanner
- [ ] Integration tests for CLI
- [ ] Achieve >80% overall coverage

### Phase 7: Configuration
- [ ] Support `.aigovern.yaml` parsing
- [ ] Add schema validation
- [ ] Config inheritance and overrides

### Phase 8: Error Handling
- [ ] Use custom exceptions everywhere
- [ ] Add helpful error messages
- [ ] Include context in exceptions

### Phase 11: Cleanup
- [ ] Delete ai_client.py
- [ ] Delete setup.py
- [ ] Update documentation (remove AIClient references)
- [ ] Remove unused imports

### Phase 12: Validation
- [ ] All tests pass
- [ ] >80% coverage
- [ ] No mypy errors
- [ ] No linting errors
- [ ] Package builds successfully
- [ ] Package passes twine check

---

## Getting Help

- **Architecture Questions:** See `docs/architecture.md`
- **Implementation Details:** See `IMPLEMENTATION_GUIDE.md`
- **Overall Plan:** See `REFACTORING_SUMMARY.md`
- **Code Examples:** Look at existing implementations:
  - `ai_governance/providers/claude.py` - Provider example
  - `ai_governance/core/base.py` - Abstract interfaces
  - `ai_governance/core/types.py` - Dataclass examples

---

## Recommended Next Action

**Start with Phase 3 (ABC Contracts) - 1 hour:**

```bash
# 1. Open PolicyEngine
code ai_governance/policy_engine.py

# 2. Add import
# from .core.base import GovernanceEngine

# 3. Update class
# class PolicyEngine(GovernanceEngine):

# 4. Update return types to match ABC
# def scan_content(self, content: str) -> List[Finding]:

# 5. Test
pytest tests/

# Repeat for Scanner, AuditLogger, ConfigManager
```

This will give you:
- ✅ Enforced interfaces
- ✅ Better type checking
- ✅ Clearer contracts
- ✅ Easier testing

Then move to Phase 6 (Tests) to lock in the improvements.

---

## Questions?

Feel free to:
1. Review the existing implementations for examples
2. Check the documentation files created
3. Run `make help` to see available commands
4. Use `git log` to see what was changed

Happy coding! 🚀
