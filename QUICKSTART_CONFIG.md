# Configuration Quick Start Guide

This guide shows you how to get started with project-specific configurations in under 5 minutes.

## Scenario: Setting Up Two Projects

### Project A: Web Application (Strict Security)

```bash
# Navigate to your web app
cd ~/projects/my-webapp

# Initialize with strict security policy
ai-governance init --project --template strict

# ✓ Created: .ai-governance/policy.yaml

# View what was configured
ai-governance config
# Shows: ✓ Project config: ~/projects/my-webapp/.ai-governance/policy.yaml

# Optional: Customize the policy
vim .ai-governance/policy.yaml

# Commit to version control
git add .ai-governance/policy.yaml
git commit -m "Add AI governance policy"

# Now refactor - automatically uses project config!
ai-governance refactor src/app.py --target "add comprehensive documentation"
```

### Project B: Internal Tool (Permissive)

```bash
# Navigate to your internal tool
cd ~/projects/internal-tool

# Initialize with permissive policy
ai-governance init --project --template permissive

# ✓ Created: .ai-governance/policy.yaml

# Refactor - automatically uses the permissive config!
ai-governance bulk-refactor src/ --target "modernize code" --lang python
```

## Scenario: User-Level Defaults

Set a default policy for all projects without their own config:

```bash
# Create user-level config (applies to all projects)
ai-governance init --user --template default-secure

# ✓ Created: ~/.config/ai-governance/policy.yaml

# Now any project without a project config uses this:
cd ~/any-project
ai-governance refactor file.py --target "..."
# Uses: ~/.config/ai-governance/policy.yaml
```

## Scenario: Team Configuration

Share a configuration with your team via git:

```bash
# Team lead creates config
cd ~/team-project
ai-governance init --project --template default-secure

# Customize for team needs
vim .ai-governance/policy.yaml

# Add to git
git add .ai-governance/policy.yaml
git commit -m "Add team AI governance policy"
git push

# Team members pull and use automatically
git pull
ai-governance refactor src/file.py --target "..."
# ✓ Automatically uses team config!
```

## Scenario: Temporary Override

Use a different policy for a one-off refactoring:

```bash
# Your project has a permissive config...
cat .ai-governance/policy.yaml  # Shows permissive

# But you want to use strict for this one file:
ai-governance refactor sensitive_file.py \
  --target "refactor" \
  --policy ~/.config/strict-temp.yaml

# Or use built-in strict template:
ai-governance refactor sensitive_file.py \
  --target "refactor" \
  --policy ai_governance/profiles/strict.yaml
```

## Configuration Hierarchy Summary

The tool searches for configs in this order (first match wins):

```
1. --policy flag         ← Explicit path (highest priority)
   ↓
2. .ai-governance/       ← Project config (current dir or parent)
   ↓
3. ~/.config/            ← User config (your personal default)
   ↓
4. Built-in              ← System default (always available)
```

## Templates Comparison

### `default-secure` (Recommended)
- **Use for**: Most projects
- **Security**: Balanced - blocks common secrets and sensitive files
- **Patterns**: Moderate restrictions
- **Best for**: General-purpose projects

### `permissive`
- **Use for**: Development, internal tools, experimentation
- **Security**: Relaxed - only blocks obvious secrets
- **Patterns**: Minimal restrictions
- **Best for**: Rapid prototyping, internal tools

### `strict`
- **Use for**: Production code, security-critical projects
- **Security**: Enhanced - extensive secret detection
- **Patterns**: Very restrictive
- **Best for**: Production applications, sensitive codebases

## Checking Your Configuration

At any time, check which config is active:

```bash
ai-governance config
```

Output:
```
Configuration Status
======================================================================

  ✓ Project config: /path/to/project/.ai-governance/policy.yaml
  ○ User config:    Not found
    Run: ai-governance init --user
  ✓ System default: /path/to/ai-governance/profiles/default-secure.yaml

Active Config:
  → /path/to/project/.ai-governance/policy.yaml
```

## Complete Workflow Example

```bash
# 1. Start new project
mkdir my-api && cd my-api
git init

# 2. Initialize AI governance
ai-governance init --project
# Chooses: default-secure template

# 3. Check configuration
ai-governance config
# Shows: Project config is active

# 4. Refactor files (config auto-detected)
ai-governance refactor src/app.py --target "modernize to Python 3.12"
# Uses: .ai-governance/policy.yaml

# 5. Bulk refactor (config auto-detected)
ai-governance bulk-refactor src/ --target "add type hints" --lang python
# Uses: .ai-governance/policy.yaml

# 6. Commit config to git
git add .ai-governance/policy.yaml
git commit -m "Add AI governance policy"

# 7. Team members benefit automatically
# When they clone the repo, config is already there!
```

## Common Commands

```bash
# Create project config
ai-governance init --project [--template TEMPLATE] [--force]

# Create user config
ai-governance init --user [--template TEMPLATE] [--force]

# Check configuration status
ai-governance config

# Refactor with auto-detected config
ai-governance refactor file.py --target "..."

# Override with explicit policy
ai-governance refactor file.py --target "..." --policy custom.yaml
```

## Troubleshooting

### "Which config is being used?"
```bash
ai-governance config
```

### "I want to change my config"
```bash
# Edit project config
vim .ai-governance/policy.yaml

# Or edit user config
vim ~/.config/ai-governance/policy.yaml
```

### "I want to use a different template"
```bash
# Overwrite with new template
ai-governance init --project --template strict --force
```

### "My team member doesn't see the config"
```bash
# Make sure they pulled the latest changes
git pull

# Check if file exists
ls -la .ai-governance/policy.yaml

# Verify it's being used
ai-governance config
```

## Next Steps

- **Customize your policy**: Edit `.ai-governance/policy.yaml` to match your needs
- **Read full guide**: See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for comprehensive documentation
- **Version control**: Add configs to git for team collaboration
- **Monitor usage**: Use `ai-governance audit` to review operations

## Summary

✅ **Project configs** (`.ai-governance/policy.yaml`) - Use for project-specific rules
✅ **User configs** (`~/.config/ai-governance/policy.yaml`) - Use for personal defaults
✅ **Explicit paths** (`--policy`) - Use for temporary overrides
✅ **Auto-discovery** - Tool automatically finds and uses the right config

**That's it! You're ready to use AI governance across all your projects.** 🎉
