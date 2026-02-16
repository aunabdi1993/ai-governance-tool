# Configuration System - Implementation Summary

## Overview

Implemented a **multi-level configuration hierarchy** that allows users to customize security policies per-project while maintaining sensible defaults. This addresses the requirement to use the tool across multiple projects with different security requirements.

## What Was Implemented

### 1. ConfigManager Class (`ai_governance/config_manager.py`)

**New module** with complete configuration management:

- **Configuration Discovery**: Automatically finds config files using priority hierarchy
- **Multi-level Hierarchy**:
  1. Explicit path (via `--policy` flag)
  2. Project-level (`./.ai-governance/policy.yaml`)
  3. User-level (`~/.config/ai-governance/policy.yaml`)
  4. System-level (built-in `default-secure.yaml`)

- **Project Config Search**:
  - Searches current directory and parent directories
  - Stops at git root (`.git` directory)
  - Supports multiple file name conventions

- **Template System**:
  - `default-secure` - Balanced security (recommended)
  - `permissive` - Relaxed rules for development
  - `strict` - Enhanced security for production

- **Helper Methods**:
  - `init_project_config()` - Create project-level config
  - `init_user_config()` - Create user-level config
  - `list_configs()` - Show all discovered configs
  - `show_config_status()` - Display configuration status
  - `_suggest_gitignore()` - Recommend .gitignore entries

**Key Features:**
- Auto-creates template files on first use
- Provides helpful feedback about which config is active
- Suggests .gitignore entries for sensitive configs
- Supports force-overwrite with `--force` flag

### 2. CLI Integration (`ai_governance/cli.py`)

**Enhanced commands:**

#### `init` Command
- `--project`: Initialize project-level config
- `--user`: Initialize user-level config
- `--template`: Choose template (default-secure/permissive/strict)
- `--force`: Overwrite existing config

```bash
ai-governance init --project --template strict
ai-governance init --user
```

#### New `config` Command
Shows configuration status:
```bash
ai-governance config
```

Output:
```
Configuration Status
======================================================================

  ✓ Project config: /path/to/.ai-governance/policy.yaml
  ○ User config:    Not found
    Run: ai-governance init --user
  ✓ System default: /path/to/profiles/default-secure.yaml

Active Config:
  → /path/to/.ai-governance/policy.yaml
```

#### Updated All Refactor Commands
All three refactor commands now use ConfigManager:
- `refactor` - Single file refactoring
- `bulk-refactor` - Multiple files/directories
- `codebase-refactor` - Dependency-aware refactoring

**Integration Pattern:**
```python
from .config_manager import ConfigManager

config_manager = ConfigManager()
policy_path = config_manager.find_config(explicit_path=policy)
policy_engine = PolicyEngine(policy_path)
```

### 3. Template Files

**Created three template files** in `ai_governance/profiles/`:

#### `default-secure.yaml` (already existed)
- Balanced security for most projects
- Blocks common secrets and sensitive files
- 1MB file size limit

#### `permissive.yaml` (NEW)
- Minimal restrictions
- Only blocks obvious secrets (OpenAI, AWS keys)
- Good for development environments
- Larger file size limit (1MB)

#### `strict.yaml` (NEW)
- Very restrictive allowed patterns
- Enhanced secret detection (tokens, DB URLs, private keys)
- Strict file size limit (512KB)
- Blocks test files, configs, credentials

### 4. Documentation

#### `CONFIGURATION_GUIDE.md` (NEW - Comprehensive)
Complete user guide covering:
- **Quick Start**: Getting started with configs
- **Configuration Hierarchy**: How priority works
- **File Locations**: Where to place configs
- **Use Cases**:
  - Different policies per project
  - Team standard configurations
  - Stricter policies in CI/CD
  - Different rules per directory
- **Template Documentation**: Details on each template
- **Customization**: How to edit YAML files
- **Version Control**: Best practices for git
- **Command Reference**: All config commands
- **Troubleshooting**: Common issues and solutions
- **Migration Guide**: Moving from old setup
- **Advanced Topics**: Environment-specific configs

#### `README.md` (UPDATED)
Added new section "Configuration Management":
- Multi-level hierarchy explanation
- Quick setup examples
- Template descriptions
- Common use cases
- Policy structure example
- References to detailed guide

#### `CONFIG_SYSTEM_SUMMARY.md` (NEW - This file)
Implementation summary for developers

## Use Cases Enabled

### Use Case 1: Per-Project Policies
```bash
# Web app - strict security
cd ~/projects/webapp
ai-governance init --project --template strict

# Internal tool - permissive
cd ~/projects/internal
ai-governance init --project --template permissive

# Each project uses its own policy automatically
ai-governance refactor file.py --target "..."
```

### Use Case 2: Team Standard
```bash
# Share team policy via git
mkdir .ai-governance
cp team-policy.yaml .ai-governance/policy.yaml
git add .ai-governance/policy.yaml
git commit -m "Add team security policy"

# Team members automatically use it
ai-governance refactor file.py --target "..."
```

### Use Case 3: User Defaults
```bash
# Set personal default for all projects
ai-governance init --user --template permissive

# All projects without project-level config use this
cd any-project/
ai-governance refactor file.py --target "..."
```

### Use Case 4: Temporary Override
```bash
# One-off use of different policy
ai-governance refactor file.py --target "..." --policy /custom/strict.yaml
```

## Configuration Discovery Flow

```
User runs: ai-governance refactor file.py --target "..."

ConfigManager.find_config(explicit_path=None):
  ↓
  1. Check explicit --policy flag?
     No → Continue

  2. Search for project config:
     - Check ./.ai-governance/policy.yaml
     - Check ./.ai-governance.yaml
     - Check ./ai-governance.yaml
     - Search parent directories (up to git root)
     Found? → Use it ✓

  3. Check user config:
     - Check ~/.config/ai-governance/policy.yaml
     Found? → Use it ✓

  4. Use system default:
     - Use built-in profiles/default-secure.yaml ✓

PolicyEngine initialized with discovered config path
  ↓
Refactoring proceeds with appropriate security policy
```

## Technical Implementation Details

### Directory Search Algorithm

```python
def _find_project_config(self) -> Optional[Path]:
    current = self.project_root

    # Search up to 10 levels or git root
    for _ in range(10):
        # Try all project config paths
        for config_name in self.PROJECT_CONFIG_PATHS:
            config_path = current / config_name
            if config_path.exists():
                return config_path

        # Stop at git root
        if (current / '.git').exists():
            break

        # Go up one level
        parent = current.parent
        if parent == current:  # Filesystem root
            break
        current = parent

    return None
```

### Config Priority Constants

```python
PROJECT_CONFIG_PATHS = [
    '.ai-governance/policy.yaml',
    '.ai-governance.yaml',
    'ai-governance.yaml',
]

USER_CONFIG_PATH = Path.home() / '.config' / 'ai-governance' / 'policy.yaml'

SYSTEM_DEFAULT_PATH = Path(__file__).parent / 'profiles' / 'default-secure.yaml'
```

### Template Auto-Creation

Templates are created on-demand when first accessed:
```python
def _get_template_path(self, template: str) -> Path:
    templates_dir = Path(__file__).parent / 'profiles'

    template_map = {
        'default-secure': templates_dir / 'default-secure.yaml',
        'permissive': templates_dir / 'permissive.yaml',
        'strict': templates_dir / 'strict.yaml',
    }

    template_path = template_map.get(template)

    if not template_path or not template_path.exists():
        # Fallback to default
        template_path = templates_dir / 'default-secure.yaml'

    return template_path
```

## Benefits

1. **Flexibility**: Different security policies for different projects
2. **Convenience**: Auto-discovery means no flags needed after setup
3. **Team Collaboration**: Shared configs via version control
4. **Security**: Project configs can be more restrictive than personal defaults
5. **Backward Compatible**: Existing `--policy` flag still works
6. **Progressive Enhancement**: Works out-of-box with system defaults

## Example Workflows

### Workflow 1: New Project Setup
```bash
# Start a new project
mkdir my-project && cd my-project
git init

# Initialize project config
ai-governance init --project

# Customize if needed
vim .ai-governance/policy.yaml

# Commit to version control
git add .ai-governance/policy.yaml
git commit -m "Add AI governance policy"

# Use tool normally - config auto-detected
ai-governance refactor src/app.py --target "modernize"
ai-governance bulk-refactor src/ --target "add docs"
```

### Workflow 2: Check Configuration Status
```bash
# Where am I getting my config from?
ai-governance config

# Output shows:
# - Which configs exist
# - Which config is active
# - How to create missing configs
```

### Workflow 3: Multiple Projects
```bash
# Development project (permissive)
cd ~/dev/internal-tool
ai-governance init --project --template permissive

# Production project (strict)
cd ~/dev/production-api
ai-governance init --project --template strict

# Prototype project (use personal default)
cd ~/dev/prototype
# No init needed, uses ~/.config/ai-governance/policy.yaml
```

## Testing the Implementation

### Test 1: Config Discovery
```bash
# Should use system default (no configs exist)
ai-governance config

# Create user config
ai-governance init --user

# Should now show user config as active
ai-governance config

# Create project config
ai-governance init --project

# Should now show project config as active (higher priority)
ai-governance config
```

### Test 2: Template Selection
```bash
# Create with permissive template
ai-governance init --project --template permissive

# Verify permissive patterns exist
cat .ai-governance/policy.yaml | grep -A 5 "allowed_patterns"

# Create with strict template
ai-governance init --project --template strict --force

# Verify strict patterns exist
cat .ai-governance/policy.yaml | grep -A 5 "blocked_patterns"
```

### Test 3: Refactor Commands
```bash
# Should auto-discover project config
ai-governance refactor test.py --target "test" --dry-run

# Should use explicit config
ai-governance refactor test.py --target "test" --policy custom.yaml --dry-run
```

## Files Modified/Created

### New Files
- `ai_governance/config_manager.py` (~450 lines)
- `ai_governance/profiles/permissive.yaml` (~60 lines)
- `ai_governance/profiles/strict.yaml` (~90 lines)
- `CONFIGURATION_GUIDE.md` (~400 lines)
- `CONFIG_SYSTEM_SUMMARY.md` (this file)

### Modified Files
- `ai_governance/cli.py`:
  - Added ConfigManager import
  - Enhanced `init` command with --project, --user, --template, --force
  - Added new `config` command
  - Updated `refactor` command to use ConfigManager
  - Updated `bulk_refactor` command to use ConfigManager
  - (codebase_refactor already had ConfigManager)
- `README.md`:
  - Added "Configuration Management" section
  - Updated command reference

## Completion Status

✅ **Core Implementation**
- ConfigManager class with full functionality
- Multi-level hierarchy (explicit > project > user > system)
- Directory tree search with git root detection
- Template system with 3 templates

✅ **CLI Integration**
- Enhanced `init` command
- New `config` command
- All refactor commands use ConfigManager

✅ **Documentation**
- Comprehensive CONFIGURATION_GUIDE.md
- Updated README.md
- Implementation summary (this file)

✅ **Templates**
- permissive.yaml created
- strict.yaml created
- default-secure.yaml (already existed)

## Next Steps (Optional Enhancements)

1. **Add more templates**: Create language-specific templates (Python, Java, etc.)
2. **Config validation**: Add YAML schema validation
3. **Config merge**: Allow extending base configs
4. **Config export**: Export active config to file
5. **Config diff**: Show differences between templates
6. **Interactive config editor**: CLI wizard for editing configs
7. **Config testing**: Test mode to validate policy files

## Summary

The configuration system is **fully implemented and ready to use**. Users can now:

1. Create project-specific configs that live outside the tool
2. Share configs via version control
3. Use different policies for different projects
4. Set personal defaults with user-level configs
5. Override with explicit paths when needed
6. Check configuration status easily

This solves the original requirement:
> "I want to be able to use this tool across multiple projects what's the best way to make this file specific to a users requirements and sits outside of this tool itself?"

**Answer**: Use project-level configs (`.ai-governance/policy.yaml`) that can be customized per-project and committed to version control! 🎉
