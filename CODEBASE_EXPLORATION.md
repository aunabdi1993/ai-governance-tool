# AI Governance Tool - Codebase Exploration Report

**Date**: 2026-02-13  
**Repository**: /Users/aunabdi/PycharmProjects/ai-governance-tool  
**Branch**: master  

## Quick Summary

The **AI Governance Tool** is a production-ready, single-file refactoring system with comprehensive security controls and audit logging. It processes one file at a time through a modular architecture using Click CLI, Anthropic Claude API, and SQLite for audit trails.

**Current State**: Single-file refactoring (no bulk processing capability)  
**Readiness for Bulk**: Components are reusable; implementation needed for directory discovery and orchestration

---

## Documentation Index

This exploration generated comprehensive documentation to understand the codebase:

### 1. **EXPLORATION_SUMMARY.txt** (14 KB)
**Executive summary with all key information**
- High-level findings and architecture overview
- Main refactoring logic locations and entry points
- CLI structure and argument parsing
- File processing approach and limitations
- Component responsibilities and interactions
- Security architecture and blocking decisions
- Data flow from input to output
- Recommendations for bulk refactoring
- Architecture summary and readiness assessment

**Read this first for a complete overview.**

### 2. **ARCHITECTURE_ANALYSIS.md** (17 KB)
**Deep technical analysis of the architecture**
- Detailed component descriptions (PolicyEngine, Scanner, AIClient, DiffManager, AuditLogger)
- CLI commands and options reference
- Current data flow with detailed steps
- Security architecture and policy management
- Refactoring prompt engineering details
- Implementation roadmap for bulk refactoring (4 phases)
- Testing strategy
- Summary tables comparing current vs. bulk needs

**Read this for architectural deep dives and implementation planning.**

### 3. **QUICK_REFERENCE.md** (13 KB)
**Quick lookup guide for developers**
- File location map with line counts
- Core components & methods (brief reference)
- CLI commands quick reference
- Complete data flow diagrams (ASCII art)
- Security flow decision trees
- Audit database schema (SQL)
- Key decision points
- Cost tracking formulas
- Common usage patterns
- Limitations and enhancement needs

**Use this as a quick reference while working with the code.**

### 4. **CODE_SNIPPETS_GUIDE.md** (22 KB)
**Complete execution traces with actual code**
- Step-by-step refactoring execution trace (12 steps)
- Complete code snippets from each component
- Policy engine security scanning code
- Audit logger querying and statistics
- Error handling examples
- Differential display implementation
- Component interaction maps

**Reference this when studying specific functions or tracing execution.**

---

## Quick Navigation

### Understanding Current Architecture
1. Start: EXPLORATION_SUMMARY.txt (sections 1-8)
2. Deep dive: ARCHITECTURE_ANALYSIS.md (sections 1-7)
3. Reference: QUICK_REFERENCE.md (sections 1-8)

### For Implementing Bulk Refactoring
1. Limitations: EXPLORATION_SUMMARY.txt (section 9)
2. Reusable components: EXPLORATION_SUMMARY.txt (section 10)
3. Roadmap: ARCHITECTURE_ANALYSIS.md (section 9)
4. Implementation guide: CODE_SNIPPETS_GUIDE.md (sections 1-5)

### For Code Review/Debugging
1. Entry points: EXPLORATION_SUMMARY.txt (section 2)
2. Data flow: QUICK_REFERENCE.md (section 8)
3. Code snippets: CODE_SNIPPETS_GUIDE.md (all sections)

---

## Key Findings at a Glance

### Architecture Type
- **Style**: Modular, component-based
- **Processing**: Sequential, single-file per invocation
- **State**: Stateless (components recreated each run)
- **Framework**: Click CLI with 3 commands

### Core Components (6)
1. **PolicyEngine** - Load and manage YAML security policies
2. **Scanner** - Validate files against policies
3. **AIClient** - Call Claude API for refactoring
4. **DiffManager** - Create diffs, backups, and manage file writes
5. **AuditLogger** - Log actions to SQLite database
6. **CLI** - Command-line interface with 3 commands

### Main Entry Point
- **File**: `ai_governance/cli.py`
- **Function**: `refactor()` (lines 153-318)
- **Flow**: Scan → Estimate Cost → Call AI → Show Diff → Backup → Apply → Audit Log

### Security Layers
1. **Path blocking** (fnmatch glob patterns)
2. **Content scanning** (regex pattern matching)
3. **Severity classification** (critical/high/medium)
4. **Audit trail** (SQLite database)

### Current Limitation
- ❌ Single file input only
- ❌ No directory support
- ❌ No glob patterns
- ❌ One CLI invocation per file
- ❌ No parallel processing
- ❌ No bulk statistics

### For Bulk Implementation
- ✅ 5/6 components fully reusable
- ✅ Architecture suitable for enhancement
- ✅ Clean interfaces for extension
- ✅ Policy engine ready for multiple files
- ✅ Audit logger designed for aggregation

---

## File Structure

```
ai-governance-tool/
├── ai_governance/
│   ├── cli.py                    # Main CLI entry point (484 lines)
│   ├── policy_engine.py          # Security policy management (126 lines)
│   ├── scanner.py                # File validation (160 lines)
│   ├── ai_client.py              # Claude API client (231 lines)
│   ├── diff_manager.py           # Diff and backup management (200 lines)
│   ├── audit_logger.py           # SQLite audit logging (237 lines)
│   └── profiles/
│       └── default-secure.yaml   # Security policy configuration
├── demo/
│   └── legacy_code/              # Test files
├── ARCHITECTURE_ANALYSIS.md      # This documentation set
├── QUICK_REFERENCE.md
├── CODE_SNIPPETS_GUIDE.md
├── EXPLORATION_SUMMARY.txt
└── [other project files]
```

---

## Next Steps for Development

### If Implementing Bulk Refactoring

**Phase 1: File Discovery**
- Create: `file_discoverer.py`
- Implement: `discover_files(directory, pattern, exclude_paths)`
- Reuse: `PolicyEngine.is_file_blocked()`

**Phase 2: Batch Processor**
- Create: `batch_processor.py`
- Implement: `BatchRefactorer` class with `process_files()`
- Reuse: `Scanner`, `AIClient`, `DiffManager`, `AuditLogger`

**Phase 3: CLI Enhancement**
- Modify: `cli.py`
- Add: New command `refactor-bulk` or `refactor --directory`
- Add: Options: `--pattern`, `--continue-on-error`, `--parallel`

**Phase 4: Reporting**
- Create: `batch_reporter.py`
- Implement: Statistics aggregation and summary reports
- Reuse: `DiffManager` for batch statistics display

**Phase 5: Testing**
- Create: `tests/test_bulk_refactoring.py`
- Test: File discovery, batch processing, error handling, aggregation

---

## Component Reference

### PolicyEngine
```
Loads YAML policy → Compiles regex patterns → Validates files
Methods: is_file_blocked(), scan_content(), get_policy_info()
Reusable: Yes, for multiple files
```

### Scanner
```
Validates single files against policy
Methods: scan_file(), format_scan_result()
Reusable: Yes, can be called in loop
Extension: Add scan_directory() for batch discovery
```

### AIClient
```
Calls Claude API for refactoring
Methods: refactor_code(), estimate_cost()
Reusable: Yes, works for any file
No changes needed for bulk
```

### DiffManager
```
Creates diffs, backups, and saves files
Methods: display_diff(), create_backup(), save_refactored()
Reusable: Yes, can process multiple files
Extension: Add aggregate_stats() for batch summaries
```

### AuditLogger
```
Logs actions to SQLite database
Methods: log_action(), get_statistics(), get_logs_by_status()
Reusable: Yes, designed for querying
Extension: Add batch query methods
```

---

## Security Model

**Blocking occurs if:**
1. File path matches blocked pattern (`**/payment*`, `**/.env*`, etc.)
2. Content has critical patterns (AWS keys, credit cards, private keys)
3. Content has high patterns (API keys, passwords, JWT tokens)

**File is allowed if:**
- No blocked patterns matched
- No sensitive content detected

**All attempts logged** with status: allowed/blocked/error/success

---

## Cost Model

**Estimation** (before API call):
- Rough: ~4 characters per token
- Estimated input: len(code + target) / 4
- Estimated output: len(code) / 4

**Actual** (after API call):
- Input cost: $3.00 per 1M tokens
- Output cost: $15.00 per 1M tokens
- Total: (input_tokens / 1M * 3.0) + (output_tokens / 1M * 15.0)

**Displayed**: Both estimated and actual costs

---

## CLI Commands

### refactor
```bash
ai-governance refactor <filepath> --target "<goal>" [options]
```
Single file refactoring with security scanning, cost estimation, diff display, backup creation, and audit logging.

### init
```bash
ai-governance init
```
Interactive API key setup (global/local/session).

### audit
```bash
ai-governance audit [--limit N] [--status STATUS] [--stats]
```
View audit logs and statistics from SQLite database.

---

## For Questions About...

**How the code flows?**
→ See QUICK_REFERENCE.md (section 8) and CODE_SNIPPETS_GUIDE.md (section 1)

**Where to modify for bulk?**
→ See EXPLORATION_SUMMARY.txt (section 5) and ARCHITECTURE_ANALYSIS.md (section 9)

**What components are reusable?**
→ See EXPLORATION_SUMMARY.txt (section 10)

**Implementation details?**
→ See CODE_SNIPPETS_GUIDE.md (all sections)

**Security architecture?**
→ See QUICK_REFERENCE.md (section 8) and ARCHITECTURE_ANALYSIS.md (section 7)

**Cost calculation?**
→ See QUICK_REFERENCE.md (section 12)

---

## Documents Summary

| Document | Size | Best For | Key Sections |
|----------|------|----------|--------------|
| EXPLORATION_SUMMARY.txt | 14 KB | Complete overview | All sections (1-14) |
| ARCHITECTURE_ANALYSIS.md | 17 KB | Deep technical dive | Sections 1-7, 9 |
| QUICK_REFERENCE.md | 13 KB | Quick lookup | Sections 1-12 |
| CODE_SNIPPETS_GUIDE.md | 22 KB | Code study & tracing | Sections 1-5 |

---

**Total Documentation**: 66 KB of comprehensive analysis  
**Code Coverage**: All 6 core components analyzed  
**Implementation Ready**: Yes, for single-file operations  
**Bulk Ready**: Yes, with enhancements  

---

For the complete exploration, start with **EXPLORATION_SUMMARY.txt**.

