# AI Governance Tool

A universal CLI tool for secure AI-assisted code refactoring across **39+ programming languages** with comprehensive security controls and audit logging.

## Overview

This tool showcases how to safely integrate AI-powered code refactoring into development workflows by:

- **Multi-Language Support**: Works with 39+ languages including Python, Java, JavaScript, TypeScript, Go, Rust, C++, and more
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
  - Original and refactored code snapshots
- **Query interface**: Filter logs by status, view statistics
- **Web Dashboard**: Visual analytics and monitoring
  - Real-time cost and token usage tracking
  - Interactive charts (day/week/month/all-time views)
  - Side-by-side code diff visualization
  - Detailed request history with filtering
  - REST API for programmatic access

### 🎨 Developer Experience

- **Interactive setup**: No manual configuration file editing required
- **Colored diff output**: Clear visualization of changes
- **Backup files**: Optional automatic backups before applying changes
- **Cost estimation**: Preview token usage before API calls
- **Interactive confirmation**: Review changes before applying
- **Secure input**: API key entry is hidden for security
- **Global installation**: Install once, use everywhere with pipx
- **Bulk operations**: Refactor entire directories or multiple files at once

## 🌐 Multi-Language Support

The tool supports **39+ programming languages** out of the box:

| Category | Languages |
|----------|-----------|
| **Web Development** | JavaScript, TypeScript, HTML, CSS, SCSS, PHP |
| **Systems Programming** | C, C++, Rust, Go |
| **JVM Languages** | Java, Kotlin, Scala, Groovy |
| **Scripting** | Python, Ruby, Perl, Shell (Bash/Zsh/Fish), Lua |
| **Functional** | Haskell, OCaml, F#, Elixir, Erlang, Clojure |
| **Mobile** | Swift, Kotlin, Dart |
| **Data & Config** | SQL, YAML, JSON, XML, Markdown, Terraform |
| **Other** | R, MATLAB, PowerShell, Vim Script, Dockerfile, Makefile |

### Language Detection

```bash
# List all supported languages
ai-governance bulk-refactor . --list-languages

# Refactor specific language(s)
ai-governance bulk-refactor src/ --lang python --target "add type hints"
ai-governance bulk-refactor src/ --lang java --lang kotlin --target "modernize"

# Refactor specific extensions
ai-governance bulk-refactor . --ext "js,jsx,ts,tsx" --target "convert to React hooks"
```

### Real-World Examples

**Java Spring Boot Project:**
```bash
ai-governance bulk-refactor src/main/java --lang java --target "add comprehensive javadoc comments"
```

**JavaScript/TypeScript React App:**
```bash
ai-governance bulk-refactor src/components --lang typescript --target "convert class components to functional"
```

**Go Microservice:**
```bash
ai-governance bulk-refactor . --lang go --target "improve error handling and add context"
```

**Multi-Language Monorepo:**
```bash
ai-governance bulk-refactor backend/ --lang python --lang java --target "add logging"
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Quick Install (Recommended)

Install globally using `pipx` for system-wide access:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install ai-governance-tool from PyPI
pipx install ai-governance-tool
```

Now `ai-governance` is available from any directory, any project!

> **Note:** The PyPI package is `ai-governance-tool` but the CLI command is `ai-governance`.

### Alternative: pip install

```bash
pip install ai-governance-tool
```

### Development Install (from source)

```bash
git clone https://github.com/aunabdi93/ai-governance-tool
cd ai-governance-tool
pip install -e .
```

### First-Time Setup

The tool will guide you through setup interactively. You have two options:

**Option 1: Run init command** (Recommended)
```bash
ai-governance init
```

This will:
- Prompt for your Anthropic API key (input is hidden for security)
- Ask where to save it (global config, local, or session-only)
- Set up everything automatically

**Option 2: Just start using it**

Simply run your first refactor command:
```bash
ai-governance refactor myfile.py --target "modernize code"
```

The tool will detect the missing API key and walk you through setup interactively!

### API Key Configuration

**Security-First Approach:**

For maximum security, the tool **does NOT save your API key to disk**. You'll be prompted to enter it when starting each session (input is hidden).

**If you prefer convenience over security**, you can set an environment variable:

```bash
# Add to your shell profile (~/.zshrc, ~/.bashrc, etc.)
export ANTHROPIC_API_KEY='your_api_key_here'
```

This way, the key is managed by your system (not by the tool), and you won't be prompted each time.

## Usage

### Global Access

Once installed with `pipx`, you can use `ai-governance` from **any directory**, with **any project**, in **any language**:

```bash
# Python project
cd ~/my-python-project
ai-governance refactor legacy.py --target "add type hints and modernize to Python 3.10+"

# Java Spring Boot project
cd ~/my-java-app
ai-governance bulk-refactor src/main/java --lang java --target "add comprehensive javadoc"

# JavaScript/TypeScript React project
cd ~/my-react-app
ai-governance refactor src/App.tsx --target "convert to functional components with hooks"

# Go microservice
cd ~/my-go-service
ai-governance bulk-refactor . --lang go --target "improve error handling with context"

# Rust project
cd ~/my-rust-project
ai-governance refactor src/main.rs --target "add better error handling and documentation"
```

The tool works seamlessly across all programming languages!

### Basic Commands

#### Refactor a file
```bash
ai-governance refactor <filepath> --target "<description>"
```

Example:
```bash
ai-governance refactor demo/legacy_code/utils.py --target "modernize to Python 3.10+ with type hints"
```

**First-time users**: If you haven't configured an API key, the tool will:
1. Detect the missing key
2. Prompt you to enter it (securely, input is hidden)
3. Use it for the current session only
4. Continue with your refactoring

**Security Note:** Your API key is NOT saved to disk. You'll be prompted again in the next session.

#### Bulk refactor multiple files or directories
```bash
ai-governance bulk-refactor <paths...> --target "<description>" [options]
```

Examples:
```bash
# Refactor entire directory (all supported languages)
ai-governance bulk-refactor src/ --target "add comprehensive documentation"

# Refactor specific language
ai-governance bulk-refactor src/ --lang python --target "add type hints"

# Refactor multiple languages
ai-governance bulk-refactor . --lang java --lang kotlin --target "modernize code"

# Refactor specific file extensions
ai-governance bulk-refactor backend/ --ext "py,pyi" --target "update to Python 3.12"

# Refactor files matching a pattern
ai-governance bulk-refactor tests/ --pattern "test_*.py" --target "use pytest fixtures"

# Mix files and directories
ai-governance bulk-refactor src/api/ lib/utils.js main.py --target "improve error handling"

# Dry run to preview what would be refactored
ai-governance bulk-refactor src/ --lang typescript --target "..." --dry-run

# Auto-apply without confirmation (use with caution)
ai-governance bulk-refactor src/ --lang go --target "..." --apply
```

**Multi-Language Project Examples:**

```bash
# Java Spring Boot - refactor all service classes
ai-governance bulk-refactor src/main/java/com/company/services \
  --lang java \
  --target "add comprehensive javadoc and improve exception handling"

# React TypeScript - convert class components to functional
ai-governance bulk-refactor src/components \
  --lang typescript \
  --pattern "*.tsx" \
  --target "convert class components to functional components with hooks"

# Go microservice - improve error handling
ai-governance bulk-refactor cmd/ internal/ \
  --lang go \
  --target "add context to errors and improve logging"

# Python data science - modernize notebooks
ai-governance bulk-refactor notebooks/ \
  --lang python \
  --pattern "*.py" \
  --target "add type hints and use modern pandas methods"
```

#### View audit logs
```bash
ai-governance audit
ai-governance audit --status blocked
ai-governance audit --stats
```

#### Launch the web dashboard
```bash
ai-governance dashboard
ai-governance dashboard --port 8080
ai-governance dashboard --host 0.0.0.0 --port 3000
```

The web dashboard provides:
- Visual analytics with interactive charts
- Cost and token usage tracking over time
- Detailed audit log viewer with filtering
- Side-by-side code diff visualization
- REST API for programmatic access

See [AUDIT_DASHBOARD.md](AUDIT_DASHBOARD.md) for complete dashboard documentation.

#### Initialize or reconfigure
```bash
ai-governance init
```

This command lets you:
- Set up your API key for the first time
- Change your existing configuration
- Switch between global and local config

### Command Options

#### `refactor` command:
- `--target, -t`: Description of desired refactoring (required)
- `--policy, -p`: Path to custom policy YAML file
- `--no-backup`: Skip creating backup files
- `--dry-run`: Scan only, don't refactor
- `--apply`: Automatically apply changes without confirmation

#### `bulk-refactor` command:
- `--target, -t`: Description of desired refactoring (required)
- `--policy, -p`: Path to custom policy YAML file
- `--lang, --language`: Filter by programming language (can specify multiple times)
- `--ext, --extensions`: Comma-separated file extensions (e.g., "py,js,ts")
- `--pattern`: Glob pattern to match files (e.g., "test_*.py")
- `--recursive/--no-recursive`: Search directories recursively (default: enabled)
- `--no-backup`: Skip creating backup files
- `--dry-run`: Scan only, don't refactor
- `--apply`: Automatically apply changes without confirmation
- `--list-languages`: Show all supported languages and exit

#### `audit` command:
- `--limit, -l`: Number of recent logs to show (default: 50)
- `--status, -s`: Filter by status (allowed/blocked/error/success)
- `--stats`: Show statistics only

#### `init` command:
- `--project`: Initialize project-level configuration (`.ai-governance/policy.yaml`)
- `--user`: Initialize user-level configuration (`~/.config/ai-governance/policy.yaml`)
- `--template`: Specify template to use (`default-secure`, `permissive`, `strict`)
- `--force`: Overwrite existing configuration file
- No options: Interactive API key setup wizard

#### `config` command:
- No options - shows configuration status and active config file

#### `sessions` command (for codebase-refactor):
- `--list`: Show all refactoring sessions with status
- `--show SESSION_ID`: Display details of a specific session
- `--cleanup`: Remove completed session checkpoints

## Demo

### Quick Start with Different Languages

Try the tool immediately with any of your projects:

```bash
# Python - Add type hints
ai-governance refactor app.py --target "add comprehensive type hints"

# Java - Add javadoc
ai-governance refactor UserService.java --target "add javadoc to all public methods"

# JavaScript - Modernize
ai-governance refactor legacy.js --target "convert to ES6+ with async/await"

# TypeScript - Improve types
ai-governance refactor api.ts --target "use strict TypeScript types"

# Go - Add error handling
ai-governance refactor handler.go --target "improve error handling with wrapped errors"

# Rust - Add documentation
ai-governance refactor main.rs --target "add comprehensive documentation comments"
```

### Security Demo

The `demo/legacy_code/` directory contains example files demonstrating the tool's security controls:

#### Files that SHOULD BE BLOCKED:

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

#### Files that SHOULD BE ALLOWED:

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

## Configuration Management

> **Quick Start**: See [QUICKSTART_CONFIG.md](QUICKSTART_CONFIG.md) for a 5-minute setup guide with examples!

### Multi-Level Configuration System

The tool uses a **flexible configuration hierarchy** that allows project-specific security policies:

**Configuration Priority (highest to lowest):**
1. **Explicit path** (`--policy custom.yaml`) - Overrides all
2. **Project-level** (`.ai-governance/policy.yaml`) - Project-specific rules
3. **User-level** (`~/.config/ai-governance/policy.yaml`) - Personal defaults
4. **System-level** (built-in `default-secure.yaml`) - Fallback

### Quick Configuration Setup

**Initialize project-specific configuration:**
```bash
# Create project config with default-secure template
ai-governance init --project

# Use permissive template for development
ai-governance init --project --template permissive

# Use strict template for production
ai-governance init --project --template strict
```

**Initialize user-level configuration:**
```bash
# Set default policy for all your projects
ai-governance init --user
```

**Check configuration status:**
```bash
ai-governance config
```

### Available Templates

1. **`default-secure`** (recommended) - Balanced security for most projects
   - Blocks common sensitive patterns
   - Allows standard source code files
   - 1MB file size limit

2. **`permissive`** - Relaxed rules for development/internal tools
   - Minimal restrictions
   - Only blocks obvious secrets
   - Good for experimentation

3. **`strict`** - Enhanced security for production code
   - Very restrictive patterns
   - Enhanced secret detection
   - 512KB file size limit

### Configuration Use Cases

**Different policies per project:**
```bash
# Web app - use strict policy
cd ~/projects/webapp
ai-governance init --project --template strict

# Internal tool - use permissive policy
cd ~/projects/internal-tool
ai-governance init --project --template permissive
```

**Team-shared configuration:**
```bash
# Copy team policy to project (commit to git)
mkdir .ai-governance
cp /path/to/team-policy.yaml .ai-governance/policy.yaml
git add .ai-governance/policy.yaml
```

**Temporary override:**
```bash
# Use explicit policy for one-off refactoring
ai-governance refactor file.py --target "..." --policy /custom/policy.yaml
```

### Policy Structure

```yaml
security:
  # Which files are allowed to be sent to AI
  allowed_patterns:
    - "**/*.py"
    - "**/*.js"
    - "src/**/*.ts"

  # Which files should never be sent
  blocked_patterns:
    - "**/.env*"
    - "**/secrets/**"
    - "**/node_modules/**"

  # Sensitive content detection
  detect_secrets:
    enabled: true
    patterns:
      - 'api[_-]?key[_-]?=.{8,}'
      - 'sk-[a-zA-Z0-9]{32,}'  # OpenAI keys

  # File size limits (bytes)
  max_file_size: 1048576  # 1MB
```

**For complete configuration documentation, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).**

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
- Verify API key is set: `echo $ANTHROPIC_API_KEY`
- Run init wizard: `ai-governance init`
- Review the default policy (bundled with package)

### Troubleshooting

**"API key not found" error:**
- The tool will automatically prompt you to enter your key
- Or set it as an environment variable: `export ANTHROPIC_API_KEY='your_key'`

**Tool not found after installation:**
- With pipx: Make sure `~/.local/bin` is in your PATH
- Run `pipx ensurepath` and restart your terminal

**Upgrade to the latest version:**
```bash
pipx upgrade ai-governance-tool
# or
pip install --upgrade ai-governance-tool
```

**Want to change API key:**
- Just enter a different key when prompted
- Or update your environment variable

**Want to use different keys for different projects:**
- Set `ANTHROPIC_API_KEY` environment variable per-project
- Or enter the appropriate key when prompted

## Quick Reference

### Common Use Cases

**Refactor entire project by language:**
```bash
ai-governance bulk-refactor . --lang <language> --target "<description>"
```

**Refactor specific directory:**
```bash
ai-governance bulk-refactor src/ --target "<description>"
```

**List all supported languages:**
```bash
ai-governance bulk-refactor . --list-languages
```

**Dry run (preview without refactoring):**
```bash
ai-governance bulk-refactor <path> --target "<description>" --dry-run
```

**View what was changed:**
```bash
ai-governance audit
ai-governance audit --stats
```

### Language-Specific Examples

| Language | Command |
|----------|---------|
| **Python** | `ai-governance bulk-refactor . --lang python --target "add type hints"` |
| **Java** | `ai-governance bulk-refactor src/main/java --lang java --target "add javadoc"` |
| **JavaScript** | `ai-governance bulk-refactor src --lang javascript --target "modernize to ES6+"` |
| **TypeScript** | `ai-governance bulk-refactor . --lang typescript --target "improve types"` |
| **Go** | `ai-governance bulk-refactor . --lang go --target "add context to errors"` |
| **Rust** | `ai-governance bulk-refactor src --lang rust --target "add documentation"` |
| **C++** | `ai-governance bulk-refactor src --lang cpp --target "modernize to C++17"` |
| **Ruby** | `ai-governance bulk-refactor lib --lang ruby --target "add yard documentation"` |

### Project Type Examples

| Project Type | Command |
|--------------|---------|
| **Spring Boot** | `ai-governance bulk-refactor src/main/java --lang java --target "add logging and javadoc"` |
| **React App** | `ai-governance bulk-refactor src --ext "jsx,tsx" --target "convert to hooks"` |
| **Django** | `ai-governance bulk-refactor . --lang python --pattern "*.py" --target "add type hints"` |
| **Node.js API** | `ai-governance bulk-refactor src --lang javascript --target "add JSDoc and error handling"` |
| **Go CLI** | `ai-governance bulk-refactor cmd --lang go --target "improve error messages"` |
| **Rust Binary** | `ai-governance bulk-refactor src --lang rust --target "add better documentation"` |

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI-powered refactoring
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Colorama](https://github.com/tartley/colorama) - Colored terminal output
- [PyYAML](https://pyyaml.org/) - YAML parsing
