# Quick Start Guide

Get up and running with AI Governance Tool in under 2 minutes.

## Step 1: Install (30 seconds)

### Recommended: Global Installation with pipx

```bash
# Install pipx (if you don't have it)
pip install pipx
pipx ensurepath

# Install ai-governance globally
pipx install /path/to/ai-governance-tool

# Verify installation
ai-governance --version
```

Now the tool is available from **any directory**!

### Alternative: Local Installation

```bash
cd ai-governance-tool
pip install -e .
```

## Step 2: First-Time Setup (1 minute)

You have two options - both are completely interactive:

### Option A: Run init (Guided Setup)

```bash
ai-governance init
```

**What happens:**
1. Asks: "Do you have your API key ready?"
2. Prompts for your API key (input is hidden)
3. Asks where to save it (global/local/session-only)
4. Done! You're ready to go.

### Option B: Jump Right In

Skip the init and just start using it:

```bash
cd ~/any-project
ai-governance refactor myfile.py --target "modernize code"
```

The tool will detect you don't have an API key and walk you through setup automatically!

## Step 3: Try It Out (30 seconds)

### Test with Demo Files

```bash
# Scan a file (no API call, free)
ai-governance refactor demo/legacy_code/utils.py \
  --target "modernize" \
  --dry-run

# Actually refactor it (uses AI)
ai-governance refactor demo/legacy_code/utils.py \
  --target "add type hints and modern Python idioms"

# Try a file with secrets (will be blocked)
ai-governance refactor demo/legacy_code/user_service.py \
  --target "refactor to FastAPI"
```

### Use with Your Own Projects

```bash
# Navigate to any project (Python, JS, Go, Java, etc.)
cd ~/my-react-app

# Refactor any file
ai-governance refactor src/App.js --target "add comments and improve readability"
```

## Step 4: View Results

```bash
# View all audit logs
ai-governance audit

# View only blocked attempts
ai-governance audit --status blocked

# View statistics
ai-governance audit --stats
```

## Common Usage Patterns

### Quick Refactoring
```bash
ai-governance refactor file.py --target "modernize" --apply
```

### Safe Testing (Dry Run)
```bash
ai-governance refactor file.py --target "test" --dry-run
```

### No Backup Needed
```bash
ai-governance refactor file.py --target "add comments" --no-backup
```

### Custom Policy
```bash
ai-governance refactor file.py --target "refactor" --policy custom.yaml
```

## Configuration Details

### Where is my API key stored?

Depends on what you chose during setup:

- **Global** (recommended): `~/.config/ai-governance/.env`
- **Local**: `./.env` in your project directory
- **Session-only**: Environment variable (not saved)

### How do I change my API key?

```bash
ai-governance init
```

Choose "yes" when asked if you want to reconfigure.

### How do I use different keys for different projects?

During setup, choose option 2 (Local) to save the API key in your project directory.

## What Gets Scanned?

The tool automatically blocks files with:

✅ **File Patterns:**
- `**/payment*`
- `**/.env*`
- `**/secrets/**`
- `**/credentials*`

✅ **Sensitive Content:**
- API keys and tokens
- Passwords
- Credit card numbers
- Private keys
- AWS/Stripe keys
- Email addresses

## Expected Behavior

### Demo Files

**These WILL BE BLOCKED** (contain sensitive data):
- `demo/legacy_code/user_service.py` - API key + password
- `demo/legacy_code/email_handler.py` - SMTP password
- `demo/legacy_code/payment_processor.py` - Credit card

**These WILL BE ALLOWED** (clean code):
- `demo/legacy_code/utils.py` - Clean utilities
- `demo/legacy_code/helper_functions.py` - Clean helpers

## Troubleshooting

### "API key not found"
Just run the command again - it will prompt you!

Or explicitly run: `ai-governance init`

### "Command not found: ai-governance"

**With pipx:**
```bash
pipx ensurepath
# Then restart your terminal
```

**With pip:**
Make sure you're in the right Python environment.

### Want to reconfigure?
```bash
ai-governance init
```

## Next Steps

✅ **Explore the demo**
```bash
python demo.py
```

✅ **Try with your own code**
```bash
cd ~/my-project
ai-governance refactor src/main.py --target "improve code quality"
```

✅ **Customize security policies**
The default policy is bundled with the package. Use `--policy` flag for custom policies.

✅ **Monitor costs and usage**
```bash
ai-governance audit --stats
```

## Full Documentation

See [README.md](README.md) for complete documentation including:
- Architecture details
- Security policy configuration
- Custom policy creation
- Advanced usage
- Best practices

---

**Total setup time: Under 2 minutes!**

The tool handles all configuration interactively - no manual file editing required.
