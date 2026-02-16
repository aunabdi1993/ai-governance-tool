# Codebase-Wide Refactoring Guide (ENHANCED)

This guide explains how to use the **advanced codebase refactoring** features that enable safe, intelligent, dependency-aware refactoring across multiple interconnected files.

## 🚀 What's New (Enhanced Features)

- **Call Graph Analysis**: Understands function call relationships, not just imports
- **Smart Context Selection**: AI-powered selection of most relevant files for context
- **Refactoring Plans**: Review and approve detailed execution plans before starting
- **Test-Driven Validation**: Automatically runs your test suite to validate changes
- **Impact Analysis**: Assess risk and understand what files will be affected
- **Checkpoint/Resume**: Save progress and resume large refactorings
- **Better Validation**: Enhanced cross-file compatibility checking

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Basic Usage](#basic-usage)
4. [Enhanced Features](#enhanced-features)
5. [Architecture](#architecture)
6. [Examples](#examples)
7. [Session Management](#session-management)
8. [Best Practices](#best-practices)

---

## Overview

The `codebase-refactor` command extends the basic `refactor` and `bulk-refactor` commands with **dependency awareness**. Instead of treating each file in isolation, it:

- **Analyzes dependencies** between files (imports, exports, function calls)
- **Groups related files** for context-aware refactoring
- **Maintains compatibility** across file boundaries
- **Validates changes** to ensure exported symbols and signatures remain compatible
- **Prevents breaking changes** in public APIs

### When to Use Codebase Refactor vs Bulk Refactor

| Feature | `bulk-refactor` | `codebase-refactor` |
|---------|----------------|---------------------|
| Files processed independently | ✅ | ❌ |
| Dependency analysis | ❌ | ✅ |
| Cross-file context in prompts | ❌ | ✅ |
| Validates compatibility | ❌ | ✅ |
| Best for isolated changes | ✅ | ❌ |
| Best for API/interface changes | ❌ | ✅ |
| Processing speed | Faster | Slower (more thorough) |

**Use `bulk-refactor` when:**
- Making purely cosmetic changes (formatting, comments)
- Updating code patterns that don't affect interfaces
- Files are independent

**Use `codebase-refactor` when:**
- Refactoring may affect function signatures
- Changing module interfaces or exports
- Files import from each other
- You need to ensure backward compatibility

---

## How It Works

The codebase refactor process has **6 phases**:

### Phase 1: Dependency Analysis
```
[1/6] Analyzing dependencies...
  ✓ Found 3 file clusters
  ✓ Determined refactoring order for 12 files
```

- **Parses imports/exports** using AST (Python) or regex (JS/TS)
- **Builds dependency graph** showing which files depend on which
- **Clusters related files** into groups
- **Determines refactoring order** using topological sort (dependencies first)

### Phase 2: Security Scanning
```
[2/6] Running security scans...
  ✓ All 12 files passed security checks
```

- Applies the same security policies as `refactor` and `bulk-refactor`
- Blocks files with sensitive content (API keys, credentials, etc.)

### Phase 3: Context-Aware Refactoring
```
[3/6] Refactoring files (with dependency awareness)...
  Processing group 1/3 (5 files)...
  Processing group 2/3 (4 files)...
  Processing group 3/3 (3 files)...
  ✓ Successfully refactored 12/12 files
```

- **Processes files in groups** based on dependencies
- **Includes related file context** in AI prompts
- **Maintains awareness** of imports and exports
- **Preserves compatibility** with dependent files

### Phase 4: Cross-File Validation
```
[4/6] Validating cross-file consistency...
  ✓ All cross-file validations passed
```

- **Checks exported symbols** haven't been removed
- **Validates function signatures** remain compatible
- **Ensures type consistency** across boundaries
- **Identifies breaking changes** before applying

### Phase 5: Type Checking (Optional)
```
[5/6] Running type checkers...
  ✓ Type checking passed
```

- Runs **mypy** for Python files (if installed)
- Runs **tsc** for TypeScript files (if installed)
- Catches type errors introduced by refactoring

### Phase 6: Apply Changes
```
[6/6] Applying changes...
  ✓ Created backups in .ai_governance_backups/20250216_143022
  ✓ Applied changes to 12 files
```

- **Creates backups** of all modified files
- **Writes refactored code** to original files
- **Logs to audit database** for tracking

---

## Basic Usage

### Command Syntax

```bash
ai-governance codebase-refactor PATHS --target "DESCRIPTION" [OPTIONS]
```

### Simple Example

Refactor all Python files in a directory:

```bash
ai-governance codebase-refactor src/ \
  --target "modernize to Python 3.12 with type hints"
```

### With File Filtering

Refactor only Python files:

```bash
ai-governance codebase-refactor . \
  --lang python \
  --target "add comprehensive docstrings"
```

### Dry Run

Preview what would change without applying:

```bash
ai-governance codebase-refactor src/ \
  --target "refactor to async/await" \
  --dry-run
```

---

## Enhanced Features

### 1. Call Graph Analysis 🔍

Beyond simple imports, the system now analyzes **actual function calls**:

**What it tracks:**
- Which functions call which other functions
- Method invocations across classes
- Hot-spot functions (most frequently called)
- Call chains and dependencies

**Why it matters:**
- Better understanding of code flow
- Identifies critical functions that need extra care
- Improves context selection for AI

### 2. Smart Context Selection 🎯

Instead of picking random related files, uses **intelligent scoring** to select the best context:

**Scoring factors:**
- Direct dependencies (imports/exports) - 100 points
- Function call relationships - 50 points per call
- Reverse dependencies (who imports this file) - 80 points
- Shared dependencies - 10 points each
- File proximity (same directory) - 20 points
- Similar naming patterns - 15 points
- Size penalty (prefers smaller files to save tokens)

**Result:** AI gets the most relevant 3-5 files (up to 6000 tokens) for optimal understanding.

### 3. Refactoring Plans 📋

Before executing, generates and displays a comprehensive plan:

```
REFACTORING PLAN
==================================================

Summary:
  Total files:  12
  Low risk:     8 files
  Medium risk:  3 files
  High risk:    1 file

Execution Order:

1. src/utils.py
   Risk: LOW
   Impact: No dependent files
   → No dependencies - safe to refactor first

2. src/models.py
   Risk: MEDIUM
   Impact: 4 file(s) will be affected
   Depends on: src/utils.py
   Used by: src/services.py, src/api.py, src/controllers.py
   → Core file - 4 file(s) depend on this
```

**You can review and approve/cancel before any changes are made.**

### 4. Test-Driven Validation ✅

Automatically detects and runs your test framework:

**Supported frameworks:**
- Python: pytest, unittest
- JavaScript/TypeScript: npm test, jest
- Go: go test
- Rust: cargo test

**What it does:**
- Runs tests after refactoring
- Parses failures and shows specific errors
- Allows you to abort if tests fail
- Counts passing tests

```bash
[7/8] Running tests...
  ✓ Tests passed
    ✓ All 47 test(s) passed
```

### 5. Change Impact Analysis 📊

Analyzes the risk and impact of each change:

**Risk Assessment:**
- **Low**: Few affected files, no breaking changes
- **Medium**: Some dependents, minor changes
- **High**: Many dependents, function removals
- **Critical**: Breaking changes affecting 10+ files

**Impact Report:**
```
CHANGE IMPACT ANALYSIS
==================================================
File: src/services.py
Risk Level: HIGH

Changes Made:
  + 25 lines added
  - 18 lines removed
  - 2 function(s) removed

Impact:
  Directly affected: 6 file(s)
    • src/api.py
    • src/controllers/user.py
    ...
  Indirectly affected: 12 file(s)

Recommendations:
  ⚠️  2 function(s) removed - verify no breaking changes
  🔴 HIGH RISK: Run comprehensive test suite before deploying
```

### 6. Checkpoint/Resume 💾

For large codebases, automatically saves progress:

**Features:**
- Auto-generates session IDs
- Saves after each file
- Resume from where you left off
- View all sessions
- Clean old sessions

**Usage:**
```bash
# Initial run (gets interrupted)
ai-governance codebase-refactor src/ --target "modernize"
# Session ID: refactor_20250216_143022_abc123
# Completed: 8/25 files

# Resume later
ai-governance codebase-refactor --resume refactor_20250216_143022_abc123 \
  --target "modernize"

# List all sessions
ai-governance sessions --list

# Clean old sessions
ai-governance sessions --clean 30
```

### 7. Enhanced Validation 🔐

Improved cross-file validation:

**Checks:**
- Syntax validity (AST parsing)
- Exported symbol compatibility
- Function signature compatibility
- Type consistency (with mypy/tsc)
- Import structure integrity

**Example:**
```python
# Before refactoring
def process_data(data: list) -> dict:
    return {"result": data}

# After refactoring - VALID (added optional param)
def process_data(data: list, options: dict = None) -> dict:
    return {"result": data, "options": options}

# After refactoring - INVALID (removed param)
def process_data() -> dict:  # ❌ Breaks compatibility!
    return {"result": []}
```

---

## Architecture

### Enhanced Module Structure

```
ai_governance/
├── dependency_analyzer.py      # Analyzes imports/exports
├── call_graph_analyzer.py      # ✨ NEW: Analyzes function calls
├── context_selector.py          # ✨ NEW: Smart context selection
├── refactor_planner.py          # ✨ NEW: Generates refactoring plans
├── test_runner.py               # ✨ NEW: Runs test suites
├── refactor_state.py            # ✨ NEW: Checkpoint/resume
├── impact_analyzer.py           # ✨ NEW: Change impact analysis
├── validators.py                # Cross-file validation
├── codebase_refactor.py         # Main orchestrator (enhanced)
└── ai_client.py                 # Extended with context-aware methods
```

### Enhanced Component Interactions

```
CLI Command
    ↓
CodebaseRefactor (orchestrator)
    ↓
    ├─→ DependencyAnalyzer (build dependency graph)
    ├─→ CallGraphAnalyzer (analyze function calls)      ✨ NEW
    ├─→ RefactorPlanner (generate execution plan)        ✨ NEW
    ├─→ Scanner (security checks)
    ├─→ ContextSelector (smart context selection)        ✨ NEW
    ├─→ AIClient (refactor with optimal context)
    ├─→ ImpactAnalyzer (assess change impact)            ✨ NEW
    ├─→ CrossFileValidator (validate changes)
    ├─→ TestRunner (run tests)                           ✨ NEW
    ├─→ TypeChecker (optional type checking)
    ├─→ RefactorState (checkpoint progress)              ✨ NEW
    └─→ AuditLogger (record actions)
```

### Processing Pipeline (8 Phases)

1. **Dependency & Call Graph Analysis** - Understand code structure
2. **Refactoring Plan Generation** - Create execution plan
3. **Security Scanning** - Block sensitive files
4. **Context-Aware Refactoring** - Refactor with smart context
5. **Impact Analysis** - Assess risks and affected files
6. **Cross-File Validation** - Ensure compatibility
7. **Test Execution** - Validate behavior
8. **Type Checking** - Optional static analysis

---

## Examples

### Example 1: Modernize Python Project

```bash
# Refactor entire Python codebase to modern standards
ai-governance codebase-refactor src/ \
  --lang python \
  --target "modernize to Python 3.12: use type hints, match statements, and dataclasses" \
  --enable-type-checking
```

**What happens:**
1. Analyzes dependencies between all Python files
2. Groups related modules together
3. Refactors each file with awareness of imported/exported symbols
4. Validates no function signatures were broken
5. Runs mypy to check types
6. Applies changes if validation passes

### Example 2: Refactor JavaScript to TypeScript

```bash
# Convert JavaScript files to TypeScript
ai-governance codebase-refactor src/ \
  --ext "js,jsx" \
  --target "convert to TypeScript with full type annotations" \
  --dry-run
```

**What happens:**
1. Finds all .js and .jsx files
2. Analyzes ES6 imports and exports
3. Shows preview of TypeScript conversions
4. Validates exported symbols remain consistent
5. Does NOT apply changes (dry run)

### Example 3: Add Comprehensive Documentation

```bash
# Add docstrings to all functions
ai-governance codebase-refactor src/ \
  --lang python \
  --target "add comprehensive Google-style docstrings to all public functions and classes"
```

**What happens:**
1. Processes Python files in dependency order
2. AI sees related files to understand context
3. Generates consistent docstring style across project
4. Validates no code changes were made (documentation only)

### Example 4: Refactor Tests

```bash
# Modernize test suite
ai-governance codebase-refactor tests/ \
  --pattern "test_*.py" \
  --target "convert to pytest fixtures and parametrize tests" \
  --no-validation
```

**What happens:**
1. Finds test files matching pattern
2. Refactors tests (validation disabled for exploratory work)
3. Creates backups before applying

### Example 5: Full-Featured Production Refactoring ✨

```bash
# Production-ready refactoring with all safety features
ai-governance codebase-refactor src/ \
  --target "refactor to async/await and add comprehensive error handling" \
  --enable-testing \
  --enable-type-checking \
  --lang python
```

**What happens (all 8 phases):**
1. **Dependency Analysis**: Builds call graph, identifies hot-spots
2. **Plan Generation**: Shows detailed plan with risk assessment, waits for approval
3. **Security Scanning**: Verifies no sensitive files
4. **Smart Refactoring**: Uses intelligent context selection (5 most relevant files per target)
5. **Impact Analysis**: Shows HIGH/MEDIUM/LOW risk for each change
6. **Cross-File Validation**: Ensures no breaking changes
7. **Test Execution**: Runs pytest automatically, shows results
8. **Type Checking**: Runs mypy for additional safety

Session is saved automatically - can resume if interrupted!

### Example 6: Resume Large Refactoring

```bash
# Start refactoring a large codebase
ai-governance codebase-refactor src/ lib/ tests/ \
  --target "modernize entire codebase" \
  --enable-testing

# Gets interrupted after 42/150 files...
# Session ID: refactor_20250216_143022_abc123

# Later, resume from checkpoint
ai-governance sessions --list
ai-governance codebase-refactor \
  --resume refactor_20250216_143022_abc123 \
  --target "modernize entire codebase"

# Continues from file 43/150!
```

---

## Session Management

### List All Sessions

View all saved refactoring sessions:

```bash
ai-governance sessions --list
```

Output:
```
Saved Refactoring Sessions
==================================================

1. refactor_20250216_143022_abc123
   2025-02-16 14:30:22
   Target: modernize to Python 3.12
   Progress: ███████████████░░░░░░░░░░░░░░░ 60.0%
   Status: IN PROGRESS (15/25 files)
   → Can resume this session

2. refactor_20250215_091512_def456
   2025-02-15 09:15:12
   Target: add type hints
   Progress: ██████████████████████████████ 100.0%
   Status: COMPLETED (48/48 files)
```

### Resume a Session

Continue where you left off:

```bash
ai-governance codebase-refactor --resume refactor_20250216_143022_abc123 \
  --target "modernize to Python 3.12"
```

The tool will:
- Load the previous state
- Show progress so far
- Continue with remaining files
- Keep the same session ID

### Delete a Session

Remove a specific session:

```bash
ai-governance sessions --delete refactor_20250216_143022_abc123
```

### Clean Old Sessions

Delete sessions older than 30 days:

```bash
ai-governance sessions --clean 30
```

### Session Files

Sessions are stored in `.ai_governance_state/` directory:
```
.ai_governance_state/
├── refactor_20250216_143022_abc123.json
├── refactor_20250215_091512_def456.json
└── refactor_20250214_163045_ghi789.json
```

Each session file contains:
- Session ID and timestamp
- List of completed files
- List of failed files
- List of pending files
- Refactoring target
- Dependency graph snapshot
- Progress statistics

---

## Best Practices

### 1. Start with Dry Runs

Always preview changes first:

```bash
ai-governance codebase-refactor src/ --target "..." --dry-run
```

### 2. Use Version Control

Ensure you have a clean git state:

```bash
git status  # Should be clean
git commit -am "Before AI refactoring"
ai-governance codebase-refactor src/ --target "..."
git diff    # Review changes
```

### 3. Refactor in Stages

For large codebases, refactor subsystems separately:

```bash
# Stage 1: Utils and helpers
ai-governance codebase-refactor src/utils/ --target "..."

# Stage 2: Models
ai-governance codebase-refactor src/models/ --target "..."

# Stage 3: Services
ai-governance codebase-refactor src/services/ --target "..."
```

### 4. Enable Type Checking for Python

Install mypy and enable type checking:

```bash
pip install mypy
ai-governance codebase-refactor src/ \
  --target "add type hints" \
  --enable-type-checking
```

### 5. Review Validation Warnings

Pay attention to warnings about dependencies:

```
⚠ src/services.py: This file is imported by 5 other files.
    Ensure compatibility is maintained.
```

### 6. Use Patterns for Targeted Refactoring

Refactor specific file types:

```bash
# Only refactor test files
ai-governance codebase-refactor tests/ --pattern "test_*.py" --target "..."

# Only refactor React components
ai-governance codebase-refactor src/ --pattern "*.tsx" --target "..."
```

### 7. Monitor Costs

The command shows total costs:

```
Total cost: $0.1234
Total tokens: 45,678
```

For large codebases, estimate first with `--dry-run`.

---

## Command Reference

### Options

| Option | Description |
|--------|-------------|
| `--target, -t` | Required. Description of refactoring goal |
| `--policy, -p` | Path to custom security policy YAML |
| `--lang` | Filter by language (python, javascript, etc.) |
| `--ext` | Filter by extensions (py,js,ts) |
| `--pattern` | File pattern to match (test_*.py) |
| `--recursive / --no-recursive` | Search directories recursively (default: yes) |
| `--dry-run` | Preview changes without applying |
| `--no-backup` | Don't create backup files |
| `--no-validation` | Skip cross-file validation |
| `--enable-type-checking` | Run mypy/tsc type checkers |

### Examples Summary

```bash
# Basic usage
ai-governance codebase-refactor src/ --target "modernize code"

# With language filter
ai-governance codebase-refactor . --lang python --target "add type hints"

# Preview only
ai-governance codebase-refactor src/ --target "..." --dry-run

# With type checking
ai-governance codebase-refactor src/ --target "..." --enable-type-checking

# Skip validation (exploratory)
ai-governance codebase-refactor src/ --target "..." --no-validation
```

---

## Troubleshooting

### Validation Failures

If validation fails:

```
✗ Validation failed with 2 errors
  - src/api.py: Removed exported symbols: handle_request
```

**Solution:** Review the refactoring goal. You may need to:
- Adjust the target description to preserve APIs
- Use `--no-validation` if breaking changes are intentional
- Manually review and fix compatibility issues

### Type Checking Errors

If type checking fails:

```
✗ Type checking failed
  - Type error: src/api.py:45: error: Incompatible return type
```

**Solution:**
- Review the type error and fix manually
- Use `--no-validation` to skip type checking
- Install/update mypy: `pip install --upgrade mypy`

### Files Not Found

```
No files found matching criteria
```

**Solution:**
- Check file paths are correct
- Verify `--lang` or `--ext` filters
- Use `--list-languages` to see supported languages

---

## Comparison: Before and After

### Before (bulk-refactor)

```bash
ai-governance bulk-refactor src/ --target "modernize code"
```

- ✅ Fast processing
- ❌ Each file refactored independently
- ❌ No dependency awareness
- ❌ May break cross-file contracts
- ❌ No validation

### After (codebase-refactor)

```bash
ai-governance codebase-refactor src/ --target "modernize code"
```

- ✅ Dependency-aware processing
- ✅ Context from related files
- ✅ Cross-file validation
- ✅ Preserves compatibility
- ⚠️ Slower (more thorough)

---

## Contributing

To extend the codebase refactor functionality:

1. **Add language support**: Extend `dependency_analyzer.py` with new language analyzers
2. **Add validators**: Extend `validators.py` with language-specific validation
3. **Improve clustering**: Enhance `DependencyAnalyzer._cluster_files()` algorithm
4. **Add metrics**: Track refactoring quality metrics in `AuditLogger`

---

## Learn More

- [Main README](README.md)
- [Security Policies](ai_governance/profiles/)
- [Architecture Documentation](ai_governance/)

---

**Happy refactoring!** 🚀
