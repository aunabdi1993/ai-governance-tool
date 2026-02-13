# AI Governance Tool - Project Summary

## What Was Built

A complete Python CLI tool demonstrating secure AI-assisted code refactoring with comprehensive security controls and audit logging.

## Project Structure

```
ai-governance-tool/
├── ai_governance/              # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # Click CLI interface
│   ├── policy_engine.py       # Policy loading and management
│   ├── scanner.py             # File and content scanning
│   ├── ai_client.py           # Anthropic API client
│   ├── diff_manager.py        # Diff display and backups
│   └── audit_logger.py        # SQLite audit logging
│
├── profiles/
│   └── default-secure.yaml    # Security policy configuration
│
├── demo/
│   └── legacy_code/           # Demo files
│       ├── user_service.py    # BLOCKED - API key, password
│       ├── email_handler.py   # BLOCKED - SMTP password, emails
│       ├── payment_processor.py # BLOCKED - credit card, payment* pattern
│       ├── utils.py           # ALLOWED - clean code
│       └── helper_functions.py # ALLOWED - clean code
│
├── demo.py                    # Python demo script
├── demo.sh                    # Shell demo script
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
├── README.md                  # Full documentation
├── QUICKSTART.md             # Quick start guide
├── LICENSE                    # MIT License
└── .gitignore                # Git ignore rules

```

## Core Features Implemented

### 1. CLI Commands (Click-based)

✅ **refactor** command:
- Scans files for security violations
- **Interactively prompts for API key if not configured**
- Sends clean code to Claude API
- Shows colored diffs
- Creates backups
- Logs all actions

✅ **init** command:
- **Interactive API key setup with hidden input**
- **Choice of global, local, or session-only configuration**
- Automatic configuration file creation
- Guided setup process

✅ **audit** command:
- Views audit logs
- Filters by status
- Shows statistics

### NEW: Interactive Configuration System

✅ **Smart API Key Detection**:
- Automatically detects missing API keys
- Prompts user interactively when needed
- No manual file editing required
- Secure input (hidden password field)

✅ **Flexible Storage Options**:
1. **Global configuration** (`~/.config/ai-governance/.env`)
   - Available from any project directory
   - Best for personal use
2. **Local configuration** (`./.env` in project)
   - Project-specific API keys
   - Good for team environments
3. **Session-only** (environment variable)
   - Not saved to disk
   - Perfect for one-time use

✅ **Package Resource Management**:
- Policy files bundled with package
- No external dependencies on file locations
- Works from any installation method

### 2. Policy Engine

✅ Loads security policies from YAML
✅ Blocks file patterns:
- `**/payment*`
- `**/.env*`
- `**/secrets/**`
- `**/credentials*`
- `**/*_secret*`

✅ Detects sensitive patterns:
- API keys (general pattern)
- Stripe API keys (sk_live_, sk_test_)
- AWS access keys (AKIA...)
- Passwords and credentials
- Email addresses
- Credit card numbers
- Private keys
- JWT tokens

### 3. Scanner Module

✅ File path pattern matching (glob-based)
✅ Content scanning with regex patterns
✅ Severity classification (critical, high, medium)
✅ Detailed findings with examples
✅ Error handling for binary files

### 4. AI Client (Anthropic SDK)

✅ Claude Sonnet 4 integration
✅ Custom refactoring prompts
✅ Token usage tracking
✅ Cost calculation
✅ Cost estimation before API calls
✅ Error handling

### 5. Diff Manager

✅ Colored diff output (red/green/cyan)
✅ Before/after comparison
✅ Change statistics (lines added/removed)
✅ Automatic backup creation with timestamps
✅ File saving with confirmation

### 6. Audit Logger (SQLite)

✅ Database schema with columns:
- timestamp
- filepath
- action
- status (allowed/blocked/error/success)
- reason
- tokens_used
- cost
- findings
- model
- target_description

✅ Query interface:
- Recent logs
- Filter by status
- Statistics view

### 7. Demo Files

✅ **Files that get BLOCKED**:
1. `user_service.py` - API key: `sk_live_51HxKj2eZvKYlo2C9x8rT3mN4pQ7wX6vU5yR8sA1bZ`, DB password: `supersecretpassword123`
2. `email_handler.py` - SMTP password: `emailpass456`, hardcoded emails
3. `payment_processor.py` - Credit card: `4532-1234-5678-9010`

✅ **Files that get ALLOWED**:
4. `utils.py` - Clean utility functions, no sensitive data
5. `helper_functions.py` - Clean helper functions, no sensitive data

## Test Results

### Demo Script Output:
```
Files allowed: 2
Files blocked: 3

Detailed Results:
  🚫 user_service.py          BLOCKED (API keys, Stripe keys, passwords)
  🚫 email_handler.py         BLOCKED (passwords, emails)
  🚫 payment_processor.py     BLOCKED (file pattern match)
  ✅ utils.py                 ALLOWED
  ✅ helper_functions.py      ALLOWED
```

### CLI Tests:

✅ Installation: `pip install -e .` - SUCCESS
✅ Version check: `ai-governance --version` - SUCCESS
✅ Help: `ai-governance --help` - SUCCESS
✅ Blocked file scan: Successfully blocked user_service.py
✅ Allowed file scan: Successfully passed utils.py
✅ Audit logs: Successfully recorded all actions
✅ Audit stats: Correctly shows 6 allowed, 6 blocked

## Key Implementation Details

### Security Pattern Matching:
- **API Keys**: `(api[_-]?key|apikey|[_-]?key)\s*[=:]\s*["']?[a-zA-Z0-9_\-]{20,}`
- **Stripe Keys**: `sk_(live|test)_[a-zA-Z0-9]{20,}`
- **Passwords**: `(password|pwd|passwd|pass)\s*[=:]\s*["']?[^\s"';]{6,}`
- **Credit Cards**: `\b(?:\d{4}[-\s]?){3}\d{4}\b`

### Cost Tracking:
- Input tokens: $3.00 per 1M tokens
- Output tokens: $15.00 per 1M tokens
- Real-time calculation and display

### Audit Database:
- SQLite database: `.ai-governance-audit.db`
- Queryable with filters
- Stores complete audit trail

## Documentation

✅ **README.md**: Complete documentation with:
- Overview and features
- Installation instructions
- Usage examples
- Demo walkthrough
- Architecture details
- Security policy configuration
- Best practices

✅ **QUICKSTART.md**: 5-minute setup guide

✅ **PROJECT_SUMMARY.md**: This document

## Dependencies

```
anthropic>=0.18.0    # Claude API client
click>=8.1.0         # CLI framework
pyyaml>=6.0          # YAML parsing
colorama>=0.4.6      # Colored output
python-dotenv>=1.0.0 # Environment variables
```

## Installation Methods

### Recommended: Global Installation with pipx
```bash
pipx install /path/to/ai-governance-tool
```

**Benefits:**
- Available from any directory, any project
- Isolated Python environment
- Works with any programming language files
- Easy to update and manage

### Alternative: Local Development Install
```bash
cd ai-governance-tool
pip install -e .
```

## Usage Examples

### First-Time Setup (Interactive):
```bash
# Option 1: Run init
ai-governance init
# Prompts for API key, asks where to save

# Option 2: Just start using it
ai-governance refactor myfile.py --target "modernize"
# Auto-detects missing API key and prompts
```

### Global Usage Across Projects:
```bash
# Works from ANY directory
cd ~/react-project
ai-governance refactor src/App.js --target "add TypeScript"

cd ~/python-project
ai-governance refactor main.py --target "modernize"

cd ~/go-project
ai-governance refactor main.go --target "improve error handling"
```

### Run Demo:
```bash
python demo.py
```

### Refactor Clean File:
```bash
ai-governance refactor demo/legacy_code/utils.py \
  --target "modernize to Python 3.10+"
```

### Try Blocked File (will fail):
```bash
ai-governance refactor demo/legacy_code/user_service.py \
  --target "refactor to FastAPI async"
```

### View Audit Logs:
```bash
ai-governance audit
ai-governance audit --status blocked
ai-governance audit --stats
```

## Success Criteria - ALL MET ✅

### Core Functionality
✅ CLI with Click framework (refactor, init, audit commands)
✅ Policy engine loading from YAML
✅ File pattern blocking (**/payment*, etc.)
✅ Sensitive content detection (API keys, passwords, etc.)
✅ Scanner checking files before AI
✅ AI client using Anthropic SDK with Claude Sonnet 4
✅ Diff manager with colored output
✅ Backup file creation
✅ SQLite audit logger with all required columns
✅ Demo files (3 blocked, 2 allowed)
✅ Correct blocking with specific reasons
✅ Token usage and cost tracking
✅ Queryable audit trail
✅ Demo script showing functionality
✅ requirements.txt with dependencies

### NEW: Enhanced User Experience
✅ Interactive API key setup (no manual file editing)
✅ Secure API key input (hidden password field)
✅ Multiple configuration options (global/local/session)
✅ Auto-detection of missing API key
✅ Inline setup during first refactor command
✅ Global installation support with pipx
✅ Package bundled policy files (importlib.resources)
✅ Multi-language support (works with any text files)
✅ Updated comprehensive documentation

## Next Steps for Users

### Quick Start (2 minutes):
1. **Install globally**: `pipx install /path/to/ai-governance-tool`
2. **Interactive setup**: `ai-governance init` (or skip - it will prompt on first use)
3. **Try it**: `ai-governance refactor demo/legacy_code/utils.py --target "modernize"`
4. **Review logs**: `ai-governance audit`

### Advanced:
- **Use with any project**: `cd ~/my-project && ai-governance refactor file.ext --target "improve"`
- **Run demo**: `python demo.py`
- **Custom policy**: `ai-governance refactor file.py --policy custom.yaml --target "refactor"`
- **Reconfigure anytime**: `ai-governance init`

## License

MIT License - See LICENSE file

## Technical Highlights

- **Modular architecture**: Separation of concerns across components
- **Interactive UX**: No manual configuration file editing required
- **Secure credential handling**: Hidden password input for API keys
- **Flexible deployment**: Global (pipx) or local installation
- **Resource bundling**: Policy files packaged with distribution
- **Multi-environment support**: Global, local, or session-only configuration
- **Comprehensive error handling**: Graceful failures with helpful messages
- **Rich user feedback**: Colored output, progress indicators, statistics
- **Audit trail**: Complete logging for compliance and debugging
- **Extensible design**: Easy to add new patterns, commands, or features
- **Production-ready patterns**: Type hints, docstrings, clean code structure
- **Language-agnostic**: Works with any text-based source files

---

**Project Status**: ✅ COMPLETE AND FULLY FUNCTIONAL

All requirements met, tested, and documented.

**Recent Enhancements** (Latest Update):
- ✅ Interactive API key management (no manual .env editing)
- ✅ Global installation support with pipx
- ✅ Auto-detection and inline setup
- ✅ Secure password input for credentials
- ✅ Multi-configuration support (global/local/session)
- ✅ Bundled policy files using importlib.resources
- ✅ Comprehensive documentation updates
