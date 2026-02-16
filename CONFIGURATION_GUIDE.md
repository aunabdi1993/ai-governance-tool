# Configuration Guide

## Overview

The AI Governance Tool uses a **multi-level configuration hierarchy** that allows you to customize security policies for different projects while maintaining sensible defaults.

## Configuration Hierarchy

The tool searches for configuration files in the following order (highest to lowest priority):

1. **Explicit path** (via `--policy` flag) - Highest priority
2. **Project-level** (`./.ai-governance/policy.yaml`) - Project-specific
3. **User-level** (`~/.config/ai-governance/policy.yaml`) - User defaults
4. **System-level** (built-in `default-secure.yaml`) - Fallback

This means:
- Project configs override user configs
- User configs override system defaults
- Explicit paths override everything

## Quick Start

### 1. Initialize Project Configuration

Create a project-specific configuration in your current directory:

```bash
ai-governance init --project
```

This creates `.ai-governance/policy.yaml` in your project directory. This file will be automatically used for all operations in this project.

**Available templates:**
- `default-secure` (recommended) - Balanced security
- `permissive` - Relaxed rules for development
- `strict` - Enhanced security for production

```bash
# Use a specific template
ai-governance init --project --template permissive

# Force overwrite existing config
ai-governance init --project --force
```

### 2. Initialize User Configuration

Create a user-level configuration that applies to all your projects:

```bash
ai-governance init --user
```

This creates `~/.config/ai-governance/policy.yaml`. This will be used as the default for all projects that don't have their own config.

### 3. Check Configuration Status

View which configuration files are active:

```bash
ai-governance config
```

Output example:
```
Configuration Status
======================================================================

  ✓ Project config: /path/to/project/.ai-governance/policy.yaml
  ○ User config:    Not found
    Run: ai-governance init --user
  ✓ System default: /path/to/profiles/default-secure.yaml

Active Config:
  → /path/to/project/.ai-governance/policy.yaml
```

## Configuration File Locations

### Project-Level Configurations

The tool searches for project configs in the current directory and parent directories (up to git root):

```
.ai-governance/policy.yaml      (recommended)
.ai-governance.yaml              (alternative)
ai-governance.yaml               (alternative)
```

**Recommended structure:**
```
my-project/
├── .ai-governance/
│   └── policy.yaml           ← Project configuration
├── .gitignore                ← Add .ai-governance/secrets.yaml
├── src/
└── tests/
```

### User-Level Configuration

Single location:
```
~/.config/ai-governance/policy.yaml
```

### System-Level (Built-in)

Bundled with the tool:
```
<package>/ai_governance/profiles/default-secure.yaml
```

## Use Cases

### Use Case 1: Different Policies Per Project

**Scenario:** You work on multiple projects with different security requirements.

**Setup:**
```bash
# Project A - Web app (strict security)
cd ~/projects/webapp
ai-governance init --project --template strict

# Project B - Internal tool (permissive)
cd ~/projects/internal-tool
ai-governance init --project --template permissive

# Project C - Open source (default)
cd ~/projects/oss-lib
ai-governance init --project
```

**Result:** Each project uses its own security policy automatically.

### Use Case 2: Team Standard Configuration

**Scenario:** Your team wants to use the same configuration across all projects.

**Setup:**
1. Create a team configuration file: `team-policy.yaml`
2. Share it via git or documentation
3. Team members reference it explicitly:

```bash
# Option 1: Use explicit path
ai-governance refactor file.py --target "..." --policy /path/to/team-policy.yaml

# Option 2: Copy to project (recommended for version control)
mkdir .ai-governance
cp /path/to/team-policy.yaml .ai-governance/policy.yaml
git add .ai-governance/policy.yaml
git commit -m "Add team security policy"

# Option 3: Use user-level for personal projects
cp /path/to/team-policy.yaml ~/.config/ai-governance/policy.yaml
```

### Use Case 3: Stricter Policies in CI/CD

**Scenario:** You want relaxed rules locally but strict rules in CI/CD.

**Setup:**

Local development:
```bash
ai-governance init --user --template permissive
```

CI/CD pipeline:
```yaml
# .github/workflows/refactor.yml
- name: Refactor with strict policy
  run: |
    ai-governance codebase-refactor src/ \
      --target "modernize" \
      --policy .github/strict-ci-policy.yaml
```

### Use Case 4: Different Rules for Different Directories

**Scenario:** Public API code needs stricter rules than internal utilities.

**Setup:**
```bash
# Root project config (permissive)
ai-governance init --project --template permissive

# API directory (strict)
cd src/api
ai-governance init --project --template strict

# Test directory (very permissive)
cd tests
ai-governance init --project --template permissive
```

**Result:** The tool searches up the directory tree and uses the nearest config.

## Configuration Templates

### Default Secure (`default-secure`)

**Recommended for:** Most projects

**Features:**
- Blocks common sensitive patterns (API keys, passwords)
- Allows all standard source code files
- Reasonable file size limits (1MB)
- Blocks test files, configs, build artifacts

### Permissive (`permissive`)

**Recommended for:** Development environments, internal tools

**Features:**
- Minimal restrictions
- Only blocks obvious secrets (OpenAI keys, AWS keys)
- Larger file size limits
- Good for experimentation

### Strict (`strict`)

**Recommended for:** Production code, security-critical projects

**Features:**
- Very restrictive allowed patterns
- Enhanced secret detection (tokens, database URLs, private keys)
- Strict file size limits (512KB)
- Blocks test files, config directories, credentials

## Customizing Configuration

### Edit Your Configuration

After initializing, edit the YAML file to customize:

```bash
# Edit project config
vim .ai-governance/policy.yaml

# Edit user config
vim ~/.config/ai-governance/policy.yaml
```

### Configuration Structure

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

### Example Customizations

#### Allow only specific directories:
```yaml
allowed_patterns:
  - "src/**/*.py"
  - "lib/**/*.py"
```

#### Block specific file types:
```yaml
blocked_patterns:
  - "**/*.min.js"        # Minified files
  - "**/*.bundle.js"     # Bundled files
  - "**/migrations/**"   # Database migrations
```

#### Custom secret patterns:
```yaml
detect_secrets:
  enabled: true
  patterns:
    - 'INTERNAL_TOKEN=[a-zA-Z0-9]+'
    - 'custom_secret_\w+'
```

## Version Control Best Practices

### What to Commit

**✅ DO commit:**
- `.ai-governance/policy.yaml` (project configuration)
- Team-shared policies
- CI/CD-specific policies

**❌ DON'T commit:**
- Files with actual secrets
- `.ai-governance/secrets.yaml` or similar sensitive files
- Personal API keys or credentials

### Gitignore Recommendations

Add to `.gitignore`:
```gitignore
# AI Governance - exclude sensitive configs
.ai-governance/secrets.yaml
.ai-governance/*.key
.ai-governance/local-*.yaml
```

The tool will suggest this when you run `ai-governance init --project`.

## Command Reference

### Initialize Commands

```bash
# Project-level
ai-governance init --project [--template TEMPLATE] [--force]

# User-level
ai-governance init --user [--template TEMPLATE] [--force]

# Templates: default-secure, permissive, strict
```

### Configuration Status

```bash
# Show all discovered configs and active config
ai-governance config
```

### Using Explicit Policy

```bash
# Any refactor command can override with --policy
ai-governance refactor file.py --target "..." --policy /custom/policy.yaml
ai-governance bulk-refactor src/ --target "..." --policy ./team-policy.yaml
ai-governance codebase-refactor src/ --target "..." --policy ../strict.yaml
```

## Troubleshooting

### "No configuration file found"

**Solution:** Initialize a configuration:
```bash
ai-governance init --project
# or
ai-governance init --user
```

### "Policy file not found"

**Problem:** You specified `--policy path` but the file doesn't exist.

**Solution:** Check the path or initialize:
```bash
ls -la .ai-governance/policy.yaml
ai-governance init --project
```

### Wrong configuration being used

**Solution:** Check priority order:
```bash
ai-governance config
```

Explicit `--policy` > Project > User > System

### Permission denied on user config

**Solution:** Ensure the directory exists:
```bash
mkdir -p ~/.config/ai-governance
chmod 755 ~/.config/ai-governance
```

## Migration from Old Setup

If you were using the built-in policy directly, migrate to project-specific configs:

### Before:
```bash
# Always used built-in default-secure.yaml
ai-governance refactor file.py --target "..."
```

### After:
```bash
# Step 1: Initialize project config
ai-governance init --project

# Step 2: Customize if needed
vim .ai-governance/policy.yaml

# Step 3: Use normally (auto-detects config)
ai-governance refactor file.py --target "..."
```

## Advanced: Environment-Specific Configs

Use environment variables to switch configurations:

```bash
# Development
export AI_GOV_POLICY=~/.config/ai-governance/dev-policy.yaml
ai-governance refactor file.py --target "..." --policy $AI_GOV_POLICY

# Production
export AI_GOV_POLICY=~/.config/ai-governance/prod-policy.yaml
ai-governance refactor file.py --target "..." --policy $AI_GOV_POLICY
```

Or use shell aliases:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias ai-gov-dev='ai-governance --policy ~/.config/ai-governance/dev.yaml'
alias ai-gov-prod='ai-governance --policy ~/.config/ai-governance/prod.yaml'

# Usage
ai-gov-dev refactor file.py --target "..."
ai-gov-prod refactor file.py --target "..."
```

## Summary

**Key Points:**
1. **Project configs** (`.ai-governance/policy.yaml`) take priority - use for project-specific rules
2. **User configs** (`~/.config/ai-governance/policy.yaml`) - use for personal defaults
3. **System defaults** are built-in - always available as fallback
4. Use `ai-governance init` to create configs
5. Use `ai-governance config` to check status
6. Use `--policy` flag to override temporarily

**Recommended Workflow:**
```bash
# For each new project
cd my-project
ai-governance init --project --template default-secure

# Customize if needed
vim .ai-governance/policy.yaml

# Commit to git
git add .ai-governance/policy.yaml
git commit -m "Add AI governance policy"

# Use normally - config auto-detected
ai-governance refactor src/file.py --target "modernize"
```

This gives you maximum flexibility while maintaining security across all your projects! 🎉
