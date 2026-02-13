# AI Governance Tool

A Python CLI tool demonstrating secure AI-assisted code refactoring with comprehensive security controls and audit logging.çç

## Overview

This tool showcases how to safely integrate AI-powered code refactoring into development workflows by:

- **Security Scanning**: Detecting sensitive content (API keys, passwords, emails, credit cards) before sending code to AI
- **Policy Enforcement**: Blocking files matching security patterns (payment systems, credentials, secrets)
- **Audit Logging**: Recording all actions, token usage, and costs in SQLite database
- **Diff Management**: Showing before/after comparisons with colored output
- **Cost Tracking**: Monitoring API token usage and estimated costs

## Features

### 🔒 Security Controls

- **Pattern-based blocking**: Blocks files matching patterns like `**/payment*`, `**/.env*`, `**/secrets/**`
- **Content scanning**: Detects sensitive data using regex patterns:
  - API keys and tokens
  - AWS access keys
  - Passwords and credentials
  - Email addresses
  - Credit card numbers
  - Private keys and JWT tokens

### 📊 Audit & Compliance

- **SQLite audit log**: Records all refactoring attempts with:
  - Timestamp, filepath, action, status
  - Reason for block/allow decisions
  - Token usage and costs
  - Security findings
- **Query interface**: Filter logs by status, view statistics

### 🎨 Developer Experience

- **Colored diff output**: Clear visualization of changes
- **Backup files**: Optional automatic backups before applying changes
- **Cost estimation**: Preview token usage before API calls
- **Interactive confirmation**: Review changes before applying

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. **Clone or download this repository**:
   ```bash
   cd ai-governance-tool
   ```

2. **Install the package**:
   ```bash
   pip install -e .
   ```

3. **Configure API key**:
   ```bash
   # Create .env file
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

   Or run the init command:
   ```bash
   ai-governance init
   ```

## Usage

### Basic Commands

#### Refactor a file
```bash
ai-governance refactor <filepath> --target "<description>"
```

Example:
```bash
ai-governance refactor demo/legacy_code/utils.py --target "modernize to Python 3.10+ with type hints"
```

#### View audit logs
```bash
ai-governance audit
ai-governance audit --status blocked
ai-governance audit --stats
```

#### Initialize configuration
```bash
ai-governance init
```

### Command Options

#### `refactor` command:
- `--target, -t`: Description of desired refactoring (required)
- `--policy, -p`: Path to custom policy YAML file
- `--no-backup`: Skip creating backup files
- `--dry-run`: Scan only, don't refactor
- `--apply`: Automatically apply changes without confirmation

#### `audit` command:
- `--limit, -l`: Number of recent logs to show (default: 50)
- `--status, -s`: Filter by status (allowed/blocked/error/success)
- `--stats`: Show statistics only

## Demo

The `demo/legacy_code/` directory contains example files demonstrating the tool's security controls:

### Files that SHOULD BE BLOCKED:

1. **user_service.py** - Contains:
   - Hardcoded API key: `sk_live_51HxKj2eZvKYlo2C9x8rT3mN4pQ7wX6vU5yR8sA1bZ`
   - Database password: `supersecretpassword123`
   - Legacy Flask synchronous code

2. **email_handler.py** - Contains:
   - SMTP password: `emailpass456`
   - Hardcoded email addresses
   - Legacy email implementation

3. **payment_processor.py** - Contains:
   - Test credit card: `4532-1234-5678-9010`
   - Payment processing code (matches `**/payment*` pattern)

### Files that SHOULD BE ALLOWED:

4. **utils.py** - Clean utility functions:
   - Date formatting and parsing
   - Username validation
   - String manipulation
   - No sensitive data

5. **helper_functions.py** - Clean helper functions:
   - List operations
   - String processing
   - Mathematical calculations
   - No sensitive data

### Running the Demo

Try refactoring the demo files to see the security controls in action:

```bash
# This will be BLOCKED - contains API key and password
ai-governance refactor demo/legacy_code/user_service.py --target "refactor to FastAPI async patterns"

# This will be BLOCKED - contains email password
ai-governance refactor demo/legacy_code/email_handler.py --target "modernize email handling"

# This will be BLOCKED - contains credit card data and matches payment* pattern
ai-governance refactor demo/legacy_code/payment_processor.py --target "update to use Stripe SDK"

# This will be ALLOWED - clean code, no sensitive data
ai-governance refactor demo/legacy_code/utils.py --target "modernize to Python 3.10+"

# This will be ALLOWED - clean code, no sensitive data
ai-governance refactor demo/legacy_code/helper_functions.py --target "use modern Python idioms"

# View audit logs to see what was blocked and why
ai-governance audit
ai-governance audit --status blocked
ai-governance audit --stats
```

## Demo Script

Run the automated demo to see all features:

```bash
python demo.py
```

Or use the shell script:

```bash
bash demo.sh
```

## Security Policy Configuration

The default security policy is defined in `profiles/default-secure.yaml`. You can customize it by:

1. Editing the default policy file
2. Creating a custom policy and using `--policy` flag

### Policy Structure

```yaml
name: "default-secure"
version: "1.0"
description: "Default security profile"

# File patterns to block
blocked_file_patterns:
  - "**/payment*"
  - "**/.env*"
  - "**/secrets/**"

# Content patterns to detect
sensitive_patterns:
  api_keys:
    pattern: '(api[_-]?key|apikey)[\s:=]["'']?[a-zA-Z0-9_\-]{20,}'
    description: "API keys and tokens"
    severity: "high"

  # ... more patterns
```

## Architecture

### Components

1. **PolicyEngine** (`policy_engine.py`): Loads and manages security policies from YAML
2. **Scanner** (`scanner.py`): Scans files for policy violations
3. **AIClient** (`ai_client.py`): Interfaces with Claude API for refactoring
4. **AuditLogger** (`audit_logger.py`): Records all actions to SQLite database
5. **DiffManager** (`diff_manager.py`): Manages diffs and backups
6. **CLI** (`cli.py`): Click-based command-line interface

### Data Flow

```
User Request
    ↓
Security Scanner (check file pattern & content)
    ↓
[BLOCKED] → Audit Log → Stop
    ↓
[ALLOWED]
    ↓
AI Client (Claude API)
    ↓
Diff Manager (show changes)
    ↓
User Confirmation
    ↓
Apply Changes + Backup
    ↓
Audit Log (success)
```

## Cost Tracking

The tool tracks and displays:
- **Estimated costs** before making API calls
- **Actual token usage** (input/output/total)
- **Per-request costs** based on Claude Sonnet 4 pricing
- **Cumulative statistics** via audit logs

Example output:
```
Estimated cost: $0.0125
Estimated tokens: ~1,250

✅ Refactoring completed!

Tokens used: 1,342
  Input:  1,105
  Output: 237
Actual cost: $0.006870
```

## Audit Database Schema

The audit log is stored in `.ai-governance-audit.db` with this schema:

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    filepath TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    findings TEXT,
    model TEXT,
    target_description TEXT
);
```

## Best Practices

1. **Review blocked files**: Always investigate why files were blocked
2. **Check audit logs regularly**: Monitor for patterns and anomalies
3. **Customize policies**: Adjust patterns based on your codebase
4. **Review diffs carefully**: Don't blindly accept AI-generated changes
5. **Keep backups enabled**: Use `--no-backup` only when appropriate
6. **Monitor costs**: Check token usage and costs in audit logs

## Limitations

- **Text files only**: Binary files are automatically rejected
- **Pattern-based detection**: May have false positives/negatives
- **No semantic analysis**: Doesn't understand context of sensitive data
- **API costs**: Each refactoring uses Claude API tokens

## Contributing

This is a demonstration tool showcasing AI governance concepts. For production use, consider:

- More sophisticated secret detection (e.g., using dedicated tools like TruffleHog)
- Integration with CI/CD pipelines
- Role-based access controls
- Encrypted audit logs
- Real-time alerts for blocked attempts

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- Check the audit logs: `ai-governance audit`
- Review the policy configuration: `profiles/default-secure.yaml`
- Verify API key is set: `echo $ANTHROPIC_API_KEY`

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered refactoring
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Colorama](https://github.com/tartley/colorama) - Colored terminal output
- [PyYAML](https://pyyaml.org/) - YAML parsing
