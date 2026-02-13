# AI Governance Tool - Refactoring Architecture Analysis

## Executive Summary

The AI Governance Tool is a **single-file refactoring system** that processes one file at a time with security scanning, AI-powered refactoring, and comprehensive audit logging. Currently, there is **no bulk/batch refactoring capability** - the system is designed for one-file-at-a-time processing.

---

## 1. CURRENT REFACTORING IMPLEMENTATION

### 1.1 Single-File Refactoring Flow

```
User Input (CLI)
    ↓
Policy Engine (Load security policy)
    ↓
Scanner (Check file for sensitive content)
    ↓
AIClient (Call Claude API for refactoring)
    ↓
DiffManager (Show changes & create backup)
    ↓
AuditLogger (Record action in SQLite)
    ↓
File Write (Save refactored code)
```

### 1.2 Main Refactoring Entry Point

**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/cli.py`

**Function**: `refactor()` (lines 153-318)

```python
@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--target', '-t', required=True, help='Description of desired refactoring')
@click.option('--policy', '-p', type=click.Path(exists=True), help='Path to policy YAML file')
@click.option('--no-backup', is_flag=True, help='Do not create backup file')
@click.option('--dry-run', is_flag=True, help='Scan only, do not refactor')
@click.option('--apply', is_flag=True, help='Automatically apply without confirmation')
def refactor(filepath, target, policy, no_backup, dry_run, apply):
    """Refactor a file using AI with security controls."""
```

### 1.3 Single-File Processing Steps

1. **Initialize Components** (lines 162-170)
   - `PolicyEngine` - Load security policy
   - `Scanner` - File security validator
   - `AuditLogger` - Track actions
   - `DiffManager` - Handle backups & diffs

2. **Security Scan** (lines 177-215)
   - `scanner.scan_file(filepath)` - Checks file against policy
   - Blocks if sensitive patterns detected
   - Logs blocked attempts to audit database

3. **Cost Estimation** (lines 244-247)
   - `ai_client.estimate_cost()` - Preview tokens & cost
   - Shows estimate before API call

4. **AI Refactoring** (lines 250-273)
   - `ai_client.refactor_code()` - Call Claude API
   - Track token usage and actual cost

5. **Diff & Backup** (lines 276-284)
   - `diff_manager.display_diff()` - Show changes
   - `diff_manager.create_backup()` - Backup original
   - `diff_manager.get_stats()` - Calculate change metrics

6. **Apply Changes** (lines 299-312)
   - `diff_manager.save_refactored()` - Write refactored code
   - Confirm with user before applying

7. **Audit Log** (lines 287-296)
   - `audit_logger.log_action()` - Record in SQLite

---

## 2. ARCHITECTURE COMPONENTS

### 2.1 Policy Engine
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/policy_engine.py`

**Key Methods**:
- `is_file_blocked(filepath)` - Check if file path matches blocked patterns
- `scan_content(content)` - Scan file content for sensitive patterns
- `get_policy_info()` - Get policy metadata

**Policy File**: `profiles/default-secure.yaml`
- Blocked file patterns: `**/payment*`, `**/.env*`, `**/secrets/**`, etc.
- Sensitive patterns: API keys, AWS keys, passwords, credit cards, PII, etc.

### 2.2 Scanner
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/scanner.py`

**Key Method**:
```python
def scan_file(self, filepath: str) -> Dict:
    """Scan a single file for policy violations."""
    # Returns: {allowed, reason, findings, file_size, error, content}
```

**Processing**:
1. Check file exists & is readable
2. Check file path patterns (using `policy_engine.is_file_blocked`)
3. Read file content (UTF-8, with error handling)
4. Scan content for sensitive patterns
5. Return results with findings

### 2.3 AI Client
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/ai_client.py`

**Key Method**:
```python
def refactor_code(self, code: str, target_description: str, filepath: str) -> Dict:
    """Refactor code using Claude API."""
    # Returns: {success, refactored_code, tokens_used, cost, model}
```

**Implementation**:
- Uses `anthropic.Anthropic` client
- Model: `claude-sonnet-4-5-20250929`
- Max tokens: 4096
- Builds custom refactoring prompt
- Calculates cost based on token usage

**Cost Calculation**:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Cost estimation before API call

### 2.4 Diff Manager
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/diff_manager.py`

**Key Methods**:
```python
def create_backup(self, filepath: str) -> Optional[str]
def generate_diff(self, original: str, refactored: str, filepath: str) -> str
def display_diff(self, original: str, refactored: str, filepath: str)
def save_refactored(self, filepath: str, refactored_code: str) -> bool
def get_stats(self, original: str, refactored: str) -> dict
def display_stats(self, stats: dict)
```

**Features**:
- Creates timestamped backups: `filename.backup_YYYYMMDD_HHMMSS.ext`
- Generates unified diff format
- Colored output (red/green/cyan)
- Statistics: lines added/removed/net change

### 2.5 Audit Logger
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/audit_logger.py`

**Database Schema** (SQLite):
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    filepath TEXT,
    action TEXT,
    status TEXT,
    reason TEXT,
    tokens_used INTEGER,
    cost REAL,
    findings TEXT,
    model TEXT,
    target_description TEXT
)
```

**Key Methods**:
```python
def log_action(...) -> int  # Log single action
def get_recent_logs(limit: int) -> List[Dict]  # Get recent logs
def get_logs_by_status(status: str) -> List[Dict]  # Filter by status
def get_statistics() -> Dict  # Summary statistics
```

**Database Location**: `.ai-governance-audit.db` (current directory)

---

## 3. CLI STRUCTURE

### 3.1 Click Command Group
**File**: `/Users/aunabdi/PycharmProjects/ai-governance-tool/ai_governance/cli.py`

**Base Command**:
```python
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AI Governance Tool - Secure AI-assisted code refactoring..."""
```

**Entry Point**: `ai_governance/cli.py::cli`

### 3.2 Available Commands

1. **`refactor`** (lines 153-318)
   - Single file refactoring
   - Arguments: `filepath`, `--target`
   - Options: `--policy`, `--no-backup`, `--dry-run`, `--apply`

2. **`init`** (lines 321-407)
   - Interactive API key setup
   - Choose configuration location (global/local/session)

3. **`audit`** (lines 416-479)
   - View audit logs
   - Options: `--limit`, `--status`, `--stats`

### 3.3 CLI Argument Parsing

```python
@click.argument('filepath', type=click.Path(exists=True))
# - Validates file exists
# - Single file only (NOT directory)

@click.option('--target', '-t', required=True)
# - Required refactoring description
# - Example: "modernize to Python 3.10+"

@click.option('--policy', '-p', type=click.Path(exists=True))
# - Optional custom policy file
# - Defaults to profiles/default-secure.yaml

@click.option('--dry-run', is_flag=True)
# - Scan only, skip refactoring

@click.option('--apply', is_flag=True)
# - Auto-apply without confirmation
```

---

## 4. FILE PROCESSING APPROACH

### 4.1 Current Single-File Processing

**Key Characteristics**:
- One `filepath` argument (validates with Click)
- No glob patterns or directory traversal
- No batch processing capability
- Sequential processing (one file per command)

**Processing Flow**:
```
CLI receives: filepath (string)
    ↓
Click validates: click.Path(exists=True)
    ↓
Scanner.scan_file(filepath) → scan_result
    ↓
if scan_result['allowed']:
    AIClient.refactor_code(...) → refactored_code
    DiffManager.create_backup(...) → backup_path
    DiffManager.save_refactored(...) → written
else:
    Log blocked attempt and return
```

### 4.2 No Bulk Processing

**Current Limitations**:
- ❌ No directory argument support
- ❌ No glob pattern matching
- ❌ No file listing/discovery
- ❌ No parallel processing
- ❌ No bulk summary/statistics
- ❌ Must invoke CLI once per file

**Example Current Usage**:
```bash
# Must run separately for each file
ai-governance refactor file1.py --target "modernize"
ai-governance refactor file2.py --target "modernize"
ai-governance refactor file3.py --target "modernize"
```

---

## 5. KEY FILES FOR MODIFICATION

### 5.1 For Adding Bulk Refactoring

| File | Purpose | Modification Area |
|------|---------|-------------------|
| `cli.py` | CLI interface | Add new `refactor-bulk` command |
| `scanner.py` | File scanning | Add `scan_directory()` method |
| `ai_client.py` | AI refactoring | No changes needed (reuse existing) |
| `diff_manager.py` | Diff/backup | Add batch statistics accumulation |
| `audit_logger.py` | Logging | Optimize for bulk logging |

### 5.2 New Components Needed

1. **Bulk File Discovery**
   - Find files in directory
   - Apply glob patterns
   - Filter by extension
   - Skip blocked paths early

2. **Bulk Processing Orchestrator**
   - Manage multiple file refactoring
   - Track progress/statistics
   - Handle errors per-file
   - Provide batch summary

3. **Batch Statistics Aggregator**
   - Total files processed
   - Success/failure counts
   - Total tokens & cost
   - Bulk change metrics

---

## 6. CURRENT DATA FLOW DETAILS

### 6.1 Scanner Output Format
```python
{
    'allowed': bool,
    'reason': str,
    'findings': [
        {
            'pattern': str,           # e.g., 'api_keys'
            'description': str,       # e.g., 'API keys and tokens'
            'severity': str,          # 'critical', 'high', 'medium'
            'match_count': int,
            'examples': [str, ...]
        }
    ],
    'file_size': int,
    'error': bool,
    'content': str  # Only if allowed=True or findings exist
}
```

### 6.2 AI Client Output Format
```python
{
    'success': bool,
    'refactored_code': str,  # If successful
    'error': str,            # If failed
    'tokens_used': {
        'input': int,
        'output': int,
        'total': int
    },
    'cost': float,
    'model': str
}
```

### 6.3 DiffManager Output
```python
stats = {
    'original_lines': int,
    'refactored_lines': int,
    'lines_added': int,
    'lines_removed': int,
    'net_change': int
}
```

---

## 7. SECURITY ARCHITECTURE

### 7.1 Security Layers

1. **File Path Blocking** (PolicyEngine)
   - Glob patterns: `**/payment*`, `**/.env*`, etc.
   - Prevents processing dangerous file types

2. **Content Scanning** (Scanner)
   - Regex pattern matching
   - Detects: API keys, passwords, credit cards, PII, etc.
   - Severity levels: critical, high, medium

3. **Policy Enforcement** (PolicyEngine)
   - Loads from YAML
   - Customizable patterns
   - Can be overridden with `--policy` flag

4. **Audit Trail** (AuditLogger)
   - SQLite database
   - Logs all attempts (allowed/blocked/error/success)
   - Tracks tokens & costs

### 7.2 Blocking Decision Tree

```
File exists & is readable?
    ├─ NO → Return error
    └─ YES

File path matches blocked patterns?
    ├─ YES → Block with reason
    └─ NO

Content has sensitive patterns?
    ├─ YES → Block with findings
    └─ NO → ALLOWED

Ready for AI refactoring
```

---

## 8. REFACTORING PROMPT ENGINEERING

### 8.1 Current Prompt Template
**Location**: `ai_client.py::_build_refactor_prompt()` (lines 154-189)

```python
prompt = f"""You are an expert code refactoring assistant. Your task is to refactor 
the provided code according to the specified requirements.

Source File: {filepath}
Refactoring Goal: {target_description}

Original Code:
```
{code}
```

Please refactor this code according to the goal. Follow these guidelines:
1. Preserve all functionality while improving code quality
2. Apply modern best practices and patterns
3. Improve readability and maintainability
4. Add appropriate comments where helpful
5. Ensure the refactored code is production-ready

Provide ONLY the refactored code in your response, without explanations or 
markdown code blocks unless they are part of the code itself."""
```

### 8.2 Current Limitations
- Generic prompt (same for all files)
- No context about refactoring style/preferences
- No batch-specific guidance
- No ability to refactor multiple related files together

---

## 9. IMPLEMENTATION ROADMAP FOR BULK REFACTORING

### Phase 1: File Discovery
```python
# Add to scanner.py or new file_discoverer.py
def discover_files(directory: str, 
                   pattern: str = "**/*.py",
                   exclude_paths: List[str] = None) -> List[str]:
    """Find files matching pattern in directory."""
    # Uses pathlib.Path.glob()
    # Filters out blocked patterns early
    # Returns: [filepath1, filepath2, ...]
```

### Phase 2: Bulk Command
```python
# Add to cli.py
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', '-g', default="**/*.py", help='File glob pattern')
@click.option('--target', '-t', required=True, help='Refactoring description')
@click.option('--policy', '-p', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True)
@click.option('--parallel', type=int, default=1, help='Parallel workers')
def refactor_bulk(directory, pattern, target, policy, dry_run, parallel):
    """Refactor multiple files in a directory."""
```

### Phase 3: Batch Processor
```python
# New: batch_processor.py
class BatchRefactorer:
    def process_files(self, 
                     files: List[str],
                     target: str,
                     policy: PolicyEngine) -> Dict:
        """Process multiple files with progress tracking."""
        # For each file:
        #   - Scan for security
        #   - Refactor if allowed
        #   - Backup & apply
        #   - Log results
        # Track: success_count, blocked_count, error_count
        # Accumulate: total_tokens, total_cost
```

### Phase 4: Results Aggregation
```python
# Update audit_logger.py
def get_bulk_statistics(action: str) -> Dict:
    """Get stats for bulk operations."""
    # Returns: {
    #   'files_processed': int,
    #   'files_allowed': int,
    #   'files_blocked': int,
    #   'files_error': int,
    #   'total_tokens': int,
    #   'total_cost': float
    # }
```

---

## 10. TESTING STRATEGY

### 10.1 Current Single-File Tests
- Manual CLI tests with demo files
- Audit log verification
- Blocked/allowed file validation

### 10.2 Bulk Testing Needs
1. **File Discovery**
   - Directory scanning
   - Pattern matching
   - Exclusion logic

2. **Batch Processing**
   - Multiple files sequentially
   - Error handling per-file
   - Partial success scenarios

3. **Statistics Aggregation**
   - Total counts
   - Cost summation
   - Status breakdown

---

## 11. SUMMARY TABLE

| Aspect | Current State | Limitation | For Bulk Needs |
|--------|---------------|-----------|----------------|
| **Input** | Single `filepath` argument | One file per invocation | Need `directory` + `pattern` |
| **Discovery** | Click validates single file | No directory traversal | Need glob file discovery |
| **Scanning** | `scan_file(filepath)` | One file at a time | Need `scan_directory()` |
| **Processing** | Sequential in CLI | No parallelism | Could add parallel workers |
| **Logging** | Per-file audit entries | Good for tracking | Need batch summary view |
| **Statistics** | Individual file stats | No aggregation | Need total cost/tokens |
| **Error Handling** | Stops on failure | One file blocks CLI | Need continue-on-error |
| **User Feedback** | Real-time per-file | Manual tracking | Need progress bar |

---

## 12. EXISTING REUSABLE COMPONENTS

The following components are **fully reusable** for bulk refactoring:

1. **PolicyEngine** ✅
   - Already handles security scanning
   - Can check multiple files
   - No changes needed

2. **Scanner** ✅
   - `scan_file()` works for any file
   - Can be called in loop
   - Add helper for directory scanning

3. **AIClient** ✅
   - `refactor_code()` handles individual files
   - Reusable for each file in batch
   - No changes needed

4. **DiffManager** ✅
   - Can backup/save multiple files
   - Can accumulate statistics
   - Add batch summary display

5. **AuditLogger** ✅
   - `log_action()` already supports batch tracking
   - Can query aggregate statistics
   - Query by action type

---

## 13. KEY FUNCTIONS TO UNDERSTAND

### Core Refactoring Flow
1. `cli.py::refactor()` - Main entry point
2. `scanner.py::scan_file()` - Security validation
3. `ai_client.py::refactor_code()` - AI processing
4. `diff_manager.py::save_refactored()` - File saving
5. `audit_logger.py::log_action()` - Recording

### For Bulk Implementation
1. Add: `file_discovery()` - Find files matching pattern
2. Add: `batch_refactor_files()` - Process file list
3. Add: `batch_statistics()` - Aggregate results
4. Extend: `audit_logger.py` - Batch queries

---

## CONCLUSION

The AI Governance Tool has a **clean, modular architecture** suitable for bulk refactoring enhancement. The main limitation is the CLI interface which currently accepts a single `filepath` argument. All core components (Scanner, AIClient, DiffManager, AuditLogger) are reusable and don't need changes.

**To add bulk refactoring**, focus on:
1. **File discovery** (directory + glob pattern)
2. **Batch orchestration** (process file list sequentially)
3. **Statistics aggregation** (total metrics)
4. **CLI enhancement** (new `refactor-bulk` command)

The existing single-file refactoring pipeline is production-ready and can be wrapped for batch operations.

