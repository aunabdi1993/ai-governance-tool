# Quick Start Guide

Get up and running with AI Governance Tool in 5 minutes.

## Installation

```bash
# Install the package
pip install -e .

# Verify installation
ai-governance --version
```

## Configuration

```bash
# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Or run init command
ai-governance init
```

## Run the Demo

```bash
# Run the security scanning demo
python demo.py

# Or use the shell script
bash demo.sh
```

This will scan all demo files and show which ones are blocked and why.

## Try It Out

### 1. Scan a file (dry run)

```bash
ai-governance refactor demo/legacy_code/utils.py \
  --target "modernize to Python 3.10+" \
  --dry-run
```

### 2. Refactor a clean file

```bash
ai-governance refactor demo/legacy_code/utils.py \
  --target "add type hints and use modern Python idioms"
```

### 3. Try to refactor a file with secrets (will be blocked)

```bash
ai-governance refactor demo/legacy_code/user_service.py \
  --target "refactor to FastAPI async"
```

This will be blocked because it contains:
- Hardcoded API key
- Database password

### 4. View audit logs

```bash
# View all logs
ai-governance audit

# View only blocked attempts
ai-governance audit --status blocked

# View statistics
ai-governance audit --stats
```

## What's Happening?

1. **Security Scanning**: Before sending code to AI, the tool:
   - Checks if file path matches blocked patterns (`**/payment*`, `**/.env*`, etc.)
   - Scans content for sensitive patterns (API keys, passwords, emails, credit cards)

2. **Blocking**: If sensitive content is found:
   - Request is blocked
   - Reason is logged to audit database
   - No API call is made

3. **Refactoring**: If file passes security checks:
   - Code is sent to Claude API
   - Refactored code is returned
   - Diff is displayed
   - User confirms before applying

4. **Audit Logging**: All actions are logged with:
   - Timestamp and filepath
   - Action and status
   - Token usage and cost
   - Security findings (if any)

## Expected Results

### Files that should be BLOCKED:

- `user_service.py` - API key, password
- `email_handler.py` - SMTP password, emails
- `payment_processor.py` - Credit card data, matches payment* pattern

### Files that should be ALLOWED:

- `utils.py` - Clean utility functions
- `helper_functions.py` - Clean helper functions

## Next Steps

1. Customize the security policy in `profiles/default-secure.yaml`
2. Add your own legacy code to refactor
3. Review audit logs regularly
4. Monitor costs via `ai-governance audit --stats`

## Common Commands

```bash
# Initialize configuration
ai-governance init

# Refactor with automatic apply
ai-governance refactor file.py --target "description" --apply

# Refactor without backup
ai-governance refactor file.py --target "description" --no-backup

# Use custom policy
ai-governance refactor file.py --target "description" --policy custom.yaml

# View recent logs
ai-governance audit --limit 20

# View statistics
ai-governance audit --stats
```

## Troubleshooting

### "API key required" error
```bash
# Set in .env file
echo "ANTHROPIC_API_KEY=your_key" > .env

# Or export in shell
export ANTHROPIC_API_KEY=your_key
```

### "Policy file not found" error
```bash
# Verify profiles directory exists
ls profiles/default-secure.yaml

# Or specify custom policy
ai-governance refactor file.py --policy /path/to/policy.yaml --target "desc"
```

### "File not found" error
```bash
# Use absolute or relative path
ai-governance refactor ./demo/legacy_code/utils.py --target "desc"
```

## More Information

See [README.md](README.md) for complete documentation.
