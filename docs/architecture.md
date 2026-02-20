# AI Governance Tool - Architecture Documentation

## Overview

The AI Governance Tool is an enterprise-grade CLI application for secure, policy-driven code refactoring using multiple AI providers (Claude, OpenAI, etc.). It follows clean architecture principles with clear separation of concerns, dependency injection, and extensibility.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐   │
│  │  CLI (Click)│  │ Web Dashboard│  │  Python API         │   │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────────────┘   │
└─────────┼────────────────┼──────────────────┼──────────────────┘
          │                │                  │
┌─────────▼────────────────▼──────────────────▼──────────────────┐
│                      Core Business Logic                        │
│  ┌──────────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│  │ Batch Processor  │  │   Scanner     │  │  PolicyEngine   │ │
│  └────────┬─────────┘  └───────┬───────┘  └────────┬────────┘ │
│           │                    │                     │          │
│  ┌────────▼──────────┐  ┌──────▼──────┐  ┌──────────▼───────┐ │
│  │CodebaseRefactor   │  │AuditLogger  │  │ ConfigManager    │ │
│  └────────┬──────────┘  └──────┬──────┘  └──────────┬────────┘ │
└───────────┼─────────────────────┼────────────────────┼──────────┘
            │                     │                    │
┌───────────▼─────────────────────▼────────────────────▼──────────┐
│                      Provider Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            ProviderFactory (Factory Pattern)             │   │
│  └───────────┬──────────────────────────────┬────────────────┘  │
│              │                              │                    │
│  ┌───────────▼──────────┐      ┌───────────▼──────────┐        │
│  │   ClaudeProvider     │      │   OpenAIProvider     │  ...   │
│  │  (Anthropic API)     │      │   (OpenAI API)       │        │
│  └──────────────────────┘      └──────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
            │                              │
┌───────────▼──────────────────────────────▼──────────────────────┐
│                      External Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Anthropic API│  │  OpenAI API  │  │  File System         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Core Layer (`ai_governance/core/`)

The core layer defines abstract interfaces and shared types.

```python
core/
├── base.py           # Abstract base classes (ABCs)
│   ├── AIProvider           # Interface for AI providers
│   ├── GovernanceEngine     # Interface for policy engines
│   ├── SecurityScanner      # Interface for security scanners
│   ├── BaseAuditLogger      # Interface for audit loggers
│   └── BaseConfigManager    # Interface for config managers
│
├── types.py          # Shared dataclasses
│   ├── RefactorResult       # Result of refactoring operation
│   ├── ScanResult           # Result of security scan
│   ├── Finding              # Security finding
│   ├── TokenUsage           # Token usage statistics
│   ├── CostEstimate         # Cost estimation
│   ├── AuditEntry           # Audit log entry
│   └── PolicyInfo           # Policy metadata
│
└── exceptions.py     # Custom exception hierarchy
    ├── AIGovernanceError    # Base exception
    ├── PolicyViolationError
    ├── SecurityViolationError
    ├── ProviderError
    │   ├── ProviderAuthError
    │   ├── ProviderRateLimitError
    │   ├── ProviderQuotaError
    │   ├── ProviderTimeoutError
    │   └── ProviderUnavailableError
    ├── ConfigError
    └── AuditError
```

### Provider Layer (`ai_governance/providers/`)

Implements the Strategy pattern for AI provider abstraction.

```python
providers/
├── factory.py        # ProviderFactory (Factory pattern)
│   └── create(provider_name, **kwargs) -> AIProvider
│
├── claude.py         # ClaudeProvider (implements AIProvider)
│   ├── refactor_code()
│   ├── refactor_with_context()
│   ├── estimate_cost()
│   └── get_model_info()
│
└── openai_provider.py # OpenAIProvider (implements AIProvider)
    ├── refactor_code()
    ├── refactor_with_context()
    ├── estimate_cost()
    └── get_model_info()
```

**Design Pattern:** Strategy + Factory

**Benefits:**
- Easy to add new providers (Gemini, Mistral, local models)
- Providers are interchangeable
- Decoupled from business logic

### Business Logic Layer

#### PolicyEngine (Governance Engine)

```python
PolicyEngine (implements GovernanceEngine)
├── Load YAML policy files
├── Compile regex patterns (cached)
├── is_file_blocked(filepath) -> (bool, reason)
├── scan_content(content) -> List[Finding]
└── get_policy_info() -> PolicyInfo
```

**Responsibilities:**
- Load and parse security policies
- Block files matching patterns
- Detect sensitive content (API keys, passwords, etc.)
- Provide policy metadata

#### Scanner (Security Scanner)

```python
Scanner (implements SecurityScanner)
├── Coordinate with PolicyEngine
├── Read file content
├── scan_file(filepath) -> ScanResult
└── Handle errors (binary files, large files, etc.)
```

**Responsibilities:**
- Orchestrate security checks
- Read file safely
- Return structured scan results

#### AuditLogger (Audit Logger)

```python
AuditLogger (implements BaseAuditLogger)
├── SQLite database backend
├── log_action(...) -> record_id
├── get_recent_logs(limit) -> List[AuditEntry]
├── get_logs_by_status(status) -> List[AuditEntry]
└── get_statistics() -> Dict[str, Any]
```

**Responsibilities:**
- Log all operations (refactor, scan, block)
- Track tokens, cost, violations
- Provide audit trail for compliance
- Generate statistics

#### ConfigManager (Configuration Manager)

```python
ConfigManager (implements BaseConfigManager)
├── Multi-level configuration priority
│   1. Explicit --policy flag
│   2. Project-level (.ai-governance/policy.yaml)
│   3. User-level (~/.config/ai-governance/policy.yaml)
│   4. System-level (bundled templates)
├── find_config(explicit_path) -> str
├── init_project_config(template) -> Path
└── init_user_config(template) -> Path
```

**Responsibilities:**
- Locate configuration files
- Initialize new configurations
- Template management

---

## Data Flow

### Single File Refactoring

```
┌──────────┐
│   User   │
└────┬─────┘
     │ ai-governance refactor file.py --target "add type hints"
     ▼
┌─────────────────┐
│   CLI (Click)   │  1. Parse arguments
└────┬────────────┘  2. Validate inputs
     │
     ▼
┌─────────────────┐
│  ConfigManager  │  3. Find policy file
└────┬────────────┘  4. Return policy path
     │
     ▼
┌─────────────────┐
│  PolicyEngine   │  5. Load policy
└────┬────────────┘  6. Compile patterns
     │
     ▼
┌─────────────────┐
│    Scanner      │  7. Check file path
└────┬────────────┘  8. Read file
     │               9. Scan content
     │               10. Return ScanResult
     ▼
┌─────────────────┐
│  Is allowed?    │
└────┬────────────┘
     │ Yes
     ▼
┌─────────────────┐
│ProviderFactory  │  11. Create provider (Claude/OpenAI)
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  AIProvider     │  12. estimate_cost()
│  (Claude/OpenAI)│  13. User confirmation
└────┬────────────┘  14. refactor_code()
     │               15. Return RefactorResult
     ▼
┌─────────────────┐
│  DiffManager    │  16. Display diff
└────┬────────────┘  17. Show statistics
     │
     ▼
┌─────────────────┐
│  AuditLogger    │  18. Log operation
└────┬────────────┘      - Tokens used
     │                   - Cost
     │                   - Violations
     ▼                   - Result
┌─────────────────┐
│ Apply changes?  │  19. User confirmation
└────┬────────────┘
     │ Yes
     ▼
┌─────────────────┐
│  DiffManager    │  20. Create backup
└────┬────────────┘  21. Write refactored code
     │
     ▼
┌──────────┐
│   Done   │
└──────────┘
```

### Batch Processing

```
User → CLI → FileDiscoverer → [list of files]
                                    │
        ┌───────────────────────────┘
        │
        ▼
    For each file:
        │
        ├─→ Scanner → ScanResult
        │       │
        │       ├─ Allowed  → Provider → RefactorResult
        │       └─ Blocked  → Log & Skip
        │
        └─→ AuditLogger → Log result
```

---

## Design Patterns

### 1. Strategy Pattern

**Where:** AI Providers

**Implementation:**
```python
class AIProvider(ABC):
    @abstractmethod
    def refactor_code(...) -> RefactorResult:
        pass

class ClaudeProvider(AIProvider):
    def refactor_code(...) -> RefactorResult:
        # Anthropic API implementation

class OpenAIProvider(AIProvider):
    def refactor_code(...) -> RefactorResult:
        # OpenAI API implementation
```

**Benefits:**
- Swap providers at runtime
- Add new providers without modifying existing code
- Test with mock providers

### 2. Factory Pattern

**Where:** ProviderFactory

**Implementation:**
```python
class ProviderFactory:
    def create(self, provider_name: str, **kwargs) -> AIProvider:
        if provider_name not in self._providers:
            raise ConfigError(...)
        return self._providers[provider_name](**kwargs)
```

**Benefits:**
- Centralized provider creation
- Easy provider registration
- Decouples client code from concrete classes

### 3. Template Method

**Where:** Abstract base classes

**Implementation:**
```python
class GovernanceEngine(ABC):
    @abstractmethod
    def scan_content(self, content: str) -> List[Finding]:
        pass
```

**Benefits:**
- Define interface contracts
- Enforce implementation requirements
- Enable polymorphism

### 4. Dependency Injection

**Where:** Throughout the codebase

**Implementation:**
```python
class BatchProcessor:
    def __init__(self, policy_engine, scanner, ai_provider, ...):
        self.policy_engine = policy_engine
        self.scanner = scanner
        self.ai_provider = ai_provider
```

**Benefits:**
- Easy testing with mocks
- Loose coupling
- Configurable dependencies

---

## Error Handling

### Exception Hierarchy

```
AIGovernanceError (base)
├── PolicyViolationError       # Policy rules violated
├── SecurityViolationError     # Security patterns detected
├── ProviderError              # AI provider errors (base)
│   ├── ProviderAuthError      # Invalid/missing API key
│   ├── ProviderRateLimitError # Rate limit exceeded
│   ├── ProviderQuotaError     # Quota exceeded
│   ├── ProviderTimeoutError   # Request timeout
│   └── ProviderUnavailableError # Service unavailable
├── ConfigError                # Configuration issues
└── AuditError                 # Audit logging failures
```

### Error Handling Strategy

1. **Catch Specific Exceptions**
   ```python
   try:
       provider = factory.create("claude")
   except ProviderAuthError as e:
       click.echo(f"Authentication failed: {e}")
       click.echo("Set ANTHROPIC_API_KEY environment variable")
   except ConfigError as e:
       click.echo(f"Configuration error: {e}")
   ```

2. **Provide Context**
   ```python
   raise ProviderAuthError(
       "Anthropic API key not found",
       details={
           "env_var": "ANTHROPIC_API_KEY",
           "docs": "https://docs.anthropic.com"
       }
   )
   ```

3. **Retry with Exponential Backoff**
   ```python
   @retry_with_backoff(max_retries=3, backoff_factor=2)
   def call_api(...):
       # API call
   ```

---

## Security Considerations

### 1. API Key Management
- Never store API keys in code
- Read from environment variables
- Prompt user if missing
- Never log API keys

### 2. File Blocking
- Block sensitive paths (`.env`, `secrets.yaml`)
- Configurable block patterns
- User can override with confirmation

### 3. Content Scanning
- Detect API keys, passwords, tokens
- Severity levels (critical, high, medium, low)
- Require approval for violations

### 4. Audit Trail
- Log all operations
- Track costs and tokens
- Record violations
- Exportable for compliance

### 5. Sandboxing
- No code execution
- Read-only by default
- Explicit confirmation for writes
- Backup before modifications

---

## Performance Optimizations

### 1. Regex Pattern Caching
```python
@lru_cache(maxsize=128)
def compile_pattern(pattern: str):
    return re.compile(pattern)
```

### 2. Lazy Initialization
- Providers created on demand
- Database connections pooled
- Configuration loaded once

### 3. Batch Processing
- Process multiple files efficiently
- Progress reporting
- Checkpointing for large jobs

### 4. Async/Await (Future)
- Parallel API calls
- Non-blocking I/O
- Improved throughput

---

## Extensibility Points

### 1. Adding a New AI Provider

See `IMPLEMENTATION_GUIDE.md` for detailed instructions.

Quick steps:
1. Create `providers/gemini.py`
2. Implement `AIProvider` interface
3. Register in `ProviderFactory`

### 2. Adding a New Security Pattern

Edit policy YAML:
```yaml
sensitive_patterns:
  - pattern: "custom_pattern_here"
    description: "Description of what it detects"
    severity: "critical"
```

### 3. Adding a New Storage Backend

Implement `BaseAuditLogger`:
```python
class PostgresAuditLogger(BaseAuditLogger):
    def log_action(...) -> int:
        # PostgreSQL implementation
```

### 4. Adding a New Configuration Source

Implement `BaseConfigManager`:
```python
class RemoteConfigManager(BaseConfigManager):
    def find_config(...) -> str:
        # Fetch from remote service
```

---

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- High coverage (>80%)

### Integration Tests
- Test component interactions
- Test CLI commands
- Test provider integration
- Database operations

### Test Doubles
- Mock API responses
- Fake file systems (pytest tmp_path)
- Stub configurations

---

## Deployment

### Package Distribution

```bash
# Build
python -m build

# Upload to PyPI
twine upload dist/*
```

### Installation

```bash
# Core package
pip install ai-governance-tool

# With OpenAI support
pip install ai-governance-tool[openai]

# With web dashboard
pip install ai-governance-tool[dashboard]

# Development setup
pip install ai-governance-tool[dev,test]
```

### Docker (Future)

```dockerfile
FROM python:3.11-slim
RUN pip install ai-governance-tool[all]
ENTRYPOINT ["ai-governance"]
```

---

## Monitoring & Observability

### Audit Logging
- All operations logged to SQLite
- JSON export for SIEM integration
- Statistics dashboard

### Metrics (Future)
- API call latency
- Token usage trends
- Cost tracking
- Error rates

### Logging Levels
- DEBUG: Detailed execution flow
- INFO: Important events
- WARNING: Potential issues
- ERROR: Operation failures

---

## Future Enhancements

1. **Async/Await**
   - Parallel processing
   - Better performance

2. **Additional Providers**
   - Google Gemini
   - Mistral AI
   - Local models (Ollama)

3. **Web UI**
   - FastAPI backend
   - React frontend
   - Real-time monitoring

4. **CI/CD Integration**
   - GitHub Actions
   - GitLab CI
   - Jenkins

5. **Advanced Features**
   - Multi-file refactoring
   - Dependency-aware refactoring
   - Test-driven refactoring
   - Impact analysis

---

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Design Patterns](https://refactoring.guru/design-patterns)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [PEP 561 - Distributing and Packaging Type Information](https://peps.python.org/pep-0561/)
