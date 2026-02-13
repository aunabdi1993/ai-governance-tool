# Quick Reference: AI Governance Tool Architecture

## File Location Map

```
/Users/aunabdi/PycharmProjects/ai-governance-tool/
├── ai_governance/
│   ├── cli.py                    [Main CLI commands - 484 lines]
│   ├── ai_client.py              [Claude API interface - 231 lines]
│   ├── scanner.py                [File security scanning - 160 lines]
│   ├── policy_engine.py          [Security policy loading - 126 lines]
│   ├── diff_manager.py           [Diff & backup management - 200 lines]
│   ├── audit_logger.py           [SQLite audit logging - 237 lines]
│   └── profiles/
│       └── default-secure.yaml   [Security policy configuration]
├── demo.py                       [Demo script]
└── demo/legacy_code/             [Test files]
    ├── user_service.py           [BLOCKED - has API keys]
    ├── email_handler.py          [BLOCKED - has passwords]
    ├── payment_processor.py      [BLOCKED - has credit cards]
    ├── utils.py                  [ALLOWED - clean code]
    └── helper_functions.py       [ALLOWED - clean code]
```

## Core Components & Methods

### 1. PolicyEngine (policy_engine.py)
```python
PolicyEngine(policy_path=None)
├── _load_policy()                    # Load YAML
├── _compile_patterns()               # Compile regex patterns
├── is_file_blocked(filepath)         # Check file path patterns
├── scan_content(content)             # Scan for sensitive patterns
├── get_cost_limits()                 # Get policy cost limits
├── get_policy_info()                 # Get policy metadata
└── [compiled_patterns dict]          # Pattern cache
```

### 2. Scanner (scanner.py)
```python
Scanner(policy_engine)
├── scan_file(filepath)               # Main scanning method
│   ├── Check file exists
│   ├── Check file path patterns
│   ├── Read file content (UTF-8)
│   ├── Scan content with policy
│   └── Return: {allowed, reason, findings, file_size, error, content}
└── format_scan_result(result, filepath)  # Format for display
```

### 3. AIClient (ai_client.py)
```python
AIClient(api_key=None, model="claude-sonnet-4-5-20250929")
├── refactor_code(code, target_description, filepath)
│   ├── Build refactoring prompt
│   ├── Call Claude API (max_tokens=4096)
│   ├── Extract refactored code
│   ├── Calculate cost & tokens
│   └── Return: {success, refactored_code, tokens_used, cost, model}
├── estimate_cost(code, target_description)  # Estimate before API call
├── _build_refactor_prompt(code, target, filepath)  # Prompt template
├── _calculate_cost(input_tokens, output_tokens)    # Cost calculation
└── _parse_api_error(error)          # User-friendly error messages
```

### 4. DiffManager (diff_manager.py)
```python
DiffManager(create_backups=True)
├── create_backup(filepath)           # Timestamp backups
├── generate_diff(original, refactored, filepath, colored=True)
├── _colorize_diff(diff_lines)        # Color output
├── display_diff(original, refactored, filepath)  # Print diff
├── get_stats(original, refactored)   # Calculate metrics
├── display_stats(stats)              # Print statistics
└── save_refactored(filepath, refactored_code)   # Write file
```

### 5. AuditLogger (audit_logger.py)
```python
AuditLogger(db_path=None)
├── _init_database()                  # Create schema
├── log_action(filepath, action, status, ...)  # Log single action
├── get_recent_logs(limit=50)         # Fetch recent logs
├── get_logs_by_status(status, limit=50)      # Filter by status
├── get_statistics()                  # Summary statistics
└── format_log_entry(entry)           # Format for display
```

## CLI Commands (cli.py)

### Command: `refactor`
```bash
ai-governance refactor <filepath> --target "<description>" [options]

Arguments:
  <filepath>              Single file to refactor

Options:
  -t, --target TEXT      Refactoring goal (required)
  -p, --policy PATH      Custom policy YAML file
  --no-backup            Skip creating backup
  --dry-run              Scan only, don't refactor
  --apply                Auto-apply without confirmation

Workflow:
  1. Load policy & components
  2. Scan file for security issues
  3. If blocked → log & stop
  4. Estimate cost
  5. Call AI for refactoring
  6. Show diff to user
  7. Create backup (unless --no-backup)
  8. Save refactored code (with confirmation or --apply)
  9. Log action to audit database
```

### Command: `init`
```bash
ai-governance init

Interactive setup:
  1. Check if API key exists
  2. Prompt for API key (hidden input)
  3. Ask where to save: global/local/session
  4. Save to chosen location
```

### Command: `audit`
```bash
ai-governance audit [options]

Options:
  -l, --limit INT        Number of logs to show (default: 50)
  -s, --status STATUS    Filter by status (allowed/blocked/error/success)
  --stats                Show statistics only

Output:
  - List of audit log entries
  - Timestamps, files, actions, costs, tokens
  - OR statistics summary (total requests, tokens, cost, status breakdown)
```

## Data Flow: Single-File Refactoring

```
USER COMMAND
  ↓
cli.refactor(filepath, target, policy, ...)
  ├─ PolicyEngine(policy) → Load security policy
  ├─ Scanner(policy_engine) → Create scanner
  ├─ AuditLogger() → Create audit logger
  ├─ DiffManager(create_backups=not no_backup) → Create diff manager
  │
  ├─ [SECURITY SCAN]
  │  └─ scanner.scan_file(filepath)
  │     ├─ Check: file exists, is file, not binary
  │     ├─ Check: file path matches blocked patterns
  │     ├─ Read: file content
  │     ├─ Scan: content against patterns
  │     └─ Return: {allowed, reason, findings, file_size, content}
  │
  ├─ IF BLOCKED:
  │  ├─ Display: ❌ BLOCKED with reason
  │  ├─ Display: Findings (critical/high patterns)
  │  ├─ Log: audit_logger.log_action(status='blocked', findings=...)
  │  └─ Exit
  │
  ├─ IF DRY-RUN:
  │  ├─ Log: audit_logger.log_action(action='scan', status='allowed')
  │  └─ Exit
  │
  ├─ [ENSURE API KEY]
  │  └─ ensure_api_key() → Prompt if missing
  │
  ├─ [COST ESTIMATION]
  │  └─ ai_client.estimate_cost(code, target)
  │     └─ Estimate tokens & cost (no API call)
  │
  ├─ [AI REFACTORING]
  │  └─ ai_client.refactor_code(code, target, filepath)
  │     ├─ Build prompt with filepath, target, code
  │     ├─ Call Claude API (max_tokens=4096)
  │     ├─ Extract refactored code
  │     ├─ Calculate: tokens_used, cost
  │     └─ Return: {success, refactored_code, tokens_used, cost, model}
  │
  ├─ [SHOW RESULTS]
  │  ├─ Display: ✅ Refactoring completed!
  │  ├─ Display: Token usage (input/output/total)
  │  ├─ Display: Actual cost
  │  ├─ diff_manager.display_diff(original, refactored, filepath)
  │  │  └─ Show unified diff with colors
  │  ├─ stats = diff_manager.get_stats(original, refactored)
  │  └─ diff_manager.display_stats(stats)
  │     └─ Show: lines added/removed/net change
  │
  ├─ [CONFIRM & APPLY]
  │  ├─ Ask: "Apply changes?" (unless --apply)
  │  │
  │  ├─ IF YES:
  │  │  ├─ diff_manager.create_backup(filepath)
  │  │  │  └─ Create: filepath.backup_YYYYMMDD_HHMMSS.ext
  │  │  ├─ diff_manager.save_refactored(filepath, refactored_code)
  │  │  │  └─ Write to file
  │  │  └─ Display: ✅ Changes applied
  │  │
  │  └─ IF NO:
  │     └─ Display: Changes not applied (file unchanged)
  │
  └─ [AUDIT LOG]
     └─ audit_logger.log_action(
        filepath=filepath,
        action='refactor',
        status='success',
        reason='Refactoring completed',
        tokens_used=total_tokens,
        cost=cost,
        model=model,
        target_description=target
     )
```

## Security Flow

```
is_file_blocked(filepath)?
  ├─ Check glob patterns:
  │  ├─ **/payment*
  │  ├─ **/.env*
  │  ├─ **/secrets/**
  │  ├─ **/credentials*
  │  └─ **/*_secret*
  ├─ YES → BLOCK with pattern reason
  └─ NO → Continue to content scan

scan_content(content)?
  ├─ Check regex patterns:
  │  ├─ api_keys (high) - [_-]?key with long value
  │  ├─ stripe_keys (critical) - sk_live/test_*
  │  ├─ aws_keys (critical) - AKIA*
  │  ├─ passwords (high) - password/pwd/pass=value
  │  ├─ emails (medium) - user@domain.ext
  │  ├─ credit_cards (critical) - \d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
  │  ├─ private_keys (critical) - -----BEGIN PRIVATE KEY-----
  │  └─ jwt_tokens (high) - eyJ*.*.*
  │
  ├─ IF found:
  │  ├─ Severity: critical/high/medium
  │  ├─ Count matches
  │  ├─ Extract examples (redacted, first 3)
  │  └─ BLOCK with finding reason
  │
  └─ NO findings → ALLOWED
```

## Audit Database Schema

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- ISO format
    filepath TEXT NOT NULL,            -- Full path to file
    action TEXT NOT NULL,              -- 'refactor', 'scan', 'init', 'audit'
    status TEXT NOT NULL,              -- 'allowed', 'blocked', 'error', 'success'
    reason TEXT,                       -- Why blocked/allowed
    tokens_used INTEGER DEFAULT 0,     -- Total tokens consumed
    cost REAL DEFAULT 0.0,             -- USD cost
    findings TEXT,                     -- Serialized security findings
    model TEXT,                        -- e.g., 'claude-sonnet-4-5-20250929'
    target_description TEXT            -- Refactoring goal
)
```

## Key Decision Points

### File Gets BLOCKED if:
1. File path matches pattern: `**/payment*`, `**/.env*`, etc.
   → Log: status='blocked', reason='File path matches blocked pattern'

2. Content contains critical pattern: API key, AWS key, credit card, private key
   → Log: status='blocked', reason='Critical: aws_keys, credit_cards', findings=[...]

3. Content contains high pattern: API key, password, JWT token
   → Log: status='blocked', reason='High: api_keys, jwt_tokens', findings=[...]

### File Gets ALLOWED if:
- No blocked file patterns match
- No sensitive content patterns detected
→ Log: status='allowed', reason='No policy violations detected'

### Refactoring Succeeds if:
- File allowed AND API call succeeds
→ Log: status='success', tokens_used=X, cost=Y, target_description=Z

## Cost Tracking

```
Estimation (before API):
  estimated_tokens = len(code + target) // 4  # Rough estimate
  estimated_cost = (tokens / 1M) * rate

Actual (after API):
  input_tokens = message.usage.input_tokens
  output_tokens = message.usage.output_tokens
  cost = (input_tokens / 1M * 3.0) + (output_tokens / 1M * 15.0)

Pricing:
  Input:  $3.00 per 1M tokens
  Output: $15.00 per 1M tokens
```

## Common Usage Patterns

```bash
# Setup (interactive)
ai-governance init

# Single file refactoring
ai-governance refactor myfile.py --target "modernize to Python 3.10+"

# Preview without applying
ai-governance refactor myfile.py --target "add type hints" --dry-run

# Auto-apply changes
ai-governance refactor myfile.py --target "improve naming" --apply

# Custom policy
ai-governance refactor myfile.py --target "refactor" --policy custom-policy.yaml

# Skip backup
ai-governance refactor myfile.py --target "refactor" --no-backup

# View audit logs
ai-governance audit
ai-governance audit --status blocked
ai-governance audit --stats
```

## Current Limitations (Single-File Only)

- Input: One `filepath` argument only
- No directory support
- No glob patterns like `**/*.py`
- No file discovery or listing
- Must invoke CLI once per file
- No batch processing
- No parallel execution
- No bulk statistics aggregation

## For Bulk Refactoring Enhancement

Would need:
1. Directory argument support: `--directory /path/to/dir`
2. File discovery: `--pattern "**/*.py"`
3. Batch orchestrator: Process file list
4. Progress tracking: Show which file being processed
5. Aggregate statistics: Total tokens, cost, changes
6. Error handling: Continue on per-file errors
7. Optional parallelization: `--parallel N`

---

**Architecture Type**: Modular, Single-file, Sequential Processing
**Framework**: Click CLI with 3 commands
**AI Provider**: Anthropic Claude API
**Database**: SQLite (audit logging)
**Security**: Pattern-based blocking (policy + content scanning)
**State**: Stateless per invocation (components recreated each run)
