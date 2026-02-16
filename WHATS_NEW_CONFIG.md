# What's New: Multi-Level Configuration System ✨

## 🎯 TL;DR

You can now use **different security policies for different projects**! Each project can have its own configuration file that lives outside the tool.

## 🚀 Quick Start

```bash
# Go to your project
cd my-project

# Initialize project-specific configuration
ai-governance init --project

# Done! Now refactor with automatic config detection
ai-governance refactor file.py --target "modernize"
```

## ✅ What You Can Do Now

### 1. Project-Specific Configurations

```bash
# Web app - use strict security
cd ~/webapp
ai-governance init --project --template strict

# Internal tool - use permissive rules
cd ~/internal-tool
ai-governance init --project --template permissive
```

Each project automatically uses its own policy!

### 2. User-Level Defaults

```bash
# Set your personal default
ai-governance init --user --template default-secure
```

All projects without their own config use this.

### 3. Check Configuration Status

```bash
ai-governance config
```

See which config is being used at any time.

### 4. Share with Team

```bash
# Config is in .ai-governance/policy.yaml
git add .ai-governance/policy.yaml
git commit -m "Add team security policy"
git push
```

Team members automatically use the team configuration.

## 📋 Available Templates

Choose the right template for your project:

| Template | Best For | Security Level |
|----------|----------|----------------|
| `default-secure` | Most projects | Balanced |
| `permissive` | Development, internal tools | Relaxed |
| `strict` | Production, sensitive code | High |

## 🔍 Configuration Priority

The tool searches for configs in this order:

```
1. --policy flag              (you specify explicitly)
   ↓
2. .ai-governance/policy.yaml (project config)
   ↓
3. ~/.config/ai-governance/   (your personal default)
   ↓
4. Built-in default           (system fallback)
```

First match wins!

## 📚 Documentation

- **5-minute guide**: [QUICKSTART_CONFIG.md](QUICKSTART_CONFIG.md)
- **Complete guide**: [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)
- **Implementation details**: [CONFIG_SYSTEM_SUMMARY.md](CONFIG_SYSTEM_SUMMARY.md)

## 🎉 Benefits

- ✨ **Different policies per project** - No more one-size-fits-all
- 🚀 **Auto-detection** - No flags needed after setup
- 👥 **Team collaboration** - Share via version control
- 🔒 **Security** - Project configs override user defaults
- ⚡ **Simple** - 5-minute setup with templates

## 📝 Common Commands

```bash
# Create project config
ai-governance init --project --template TEMPLATE

# Create user config
ai-governance init --user

# Check what's active
ai-governance config

# Refactor (auto-detects config)
ai-governance refactor file.py --target "..."

# Override temporarily
ai-governance refactor file.py --target "..." --policy custom.yaml
```

## 🆕 What Changed

**New Features:**
- Multi-level configuration hierarchy
- Auto-discovery of project configs
- Three security templates (default-secure, permissive, strict)
- `config` command to show status
- Enhanced `init` command with templates

**New Commands:**
- `ai-governance init --project` - Create project config
- `ai-governance init --user` - Create user config
- `ai-governance config` - Show configuration status

**Files Created:**
- `.ai-governance/policy.yaml` - Project config (when you run init)
- `~/.config/ai-governance/policy.yaml` - User config (optional)

## 💡 Example Workflows

### Workflow 1: New Project
```bash
cd my-new-project
ai-governance init --project
git add .ai-governance/policy.yaml
git commit -m "Add AI governance policy"

# Now refactor automatically uses project config
ai-governance refactor src/*.py --target "modernize"
```

### Workflow 2: Different Projects
```bash
# Production API - strict
cd api && ai-governance init --project --template strict

# Prototype - permissive
cd prototype && ai-governance init --project --template permissive

# Each uses its own policy automatically!
```

### Workflow 3: Team Configuration
```bash
# Team lead sets up config
cd team-repo
ai-governance init --project
git push

# Team members pull and use automatically
git pull
ai-governance refactor file.py --target "..."  # Just works!
```

## ❓ FAQ

**Q: Do I need to specify `--policy` every time now?**
A: No! After running `ai-governance init --project`, the tool auto-detects your config.

**Q: Can I still use `--policy` flag?**
A: Yes! It overrides everything if you need a one-off different policy.

**Q: What if I don't create any config?**
A: The tool uses the built-in `default-secure.yaml` as fallback. It just works!

**Q: Can I customize the templates?**
A: Yes! After running `init`, edit `.ai-governance/policy.yaml` to your needs.

**Q: Should I commit the config to git?**
A: Yes! That way your team uses the same policy automatically.

## 🎊 Ready to Use!

The configuration system is fully implemented and tested. Start using it now:

```bash
ai-governance init --project
```

That's it! Your project now has its own security policy. 🚀
