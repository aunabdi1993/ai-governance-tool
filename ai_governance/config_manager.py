"""Configuration manager for AI Governance Tool.

Handles multi-level configuration discovery and management:
1. Project-level: ./.ai-governance/policy.yaml (highest priority)
2. User-level: ~/.config/ai-governance/policy.yaml
3. System-level: Built-in defaults (fallback)
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, List
import click
from colorama import Fore, Style


class ConfigManager:
    """Manages configuration files across multiple levels."""

    # Configuration search paths (in order of priority)
    PROJECT_CONFIG_PATHS = [
        '.ai-governance/policy.yaml',
        '.ai-governance.yaml',
        'ai-governance.yaml',
    ]

    USER_CONFIG_PATH = Path.home() / '.config' / 'ai-governance' / 'policy.yaml'

    # Built-in default (inside package)
    SYSTEM_DEFAULT_PATH = Path(__file__).parent / 'profiles' / 'default-secure.yaml'

    def __init__(self, project_root: str = "."):
        """
        Initialize config manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()

    def find_config(self, explicit_path: Optional[str] = None) -> str:
        """
        Find configuration file using priority hierarchy.

        Priority order:
        1. Explicit path (from --policy flag)
        2. Project-level config (./.ai-governance/policy.yaml)
        3. User-level config (~/.config/ai-governance/policy.yaml)
        4. System default (built-in)

        Args:
            explicit_path: Path provided via --policy flag

        Returns:
            Path to configuration file to use
        """
        # 1. Explicit path has highest priority
        if explicit_path:
            explicit = Path(explicit_path)
            if explicit.exists():
                click.echo(f"  Using explicit policy: {explicit}")
                return str(explicit)
            else:
                click.echo(f"{Fore.RED}✗ Policy file not found: {explicit}{Style.RESET_ALL}")
                raise FileNotFoundError(f"Policy file not found: {explicit}")

        # 2. Project-level config
        project_config = self._find_project_config()
        if project_config:
            click.echo(f"  Using project policy: {project_config}")
            return str(project_config)

        # 3. User-level config
        if self.USER_CONFIG_PATH.exists():
            click.echo(f"  Using user policy: {self.USER_CONFIG_PATH}")
            return str(self.USER_CONFIG_PATH)

        # 4. System default
        if self.SYSTEM_DEFAULT_PATH.exists():
            click.echo(f"  Using system default policy")
            return str(self.SYSTEM_DEFAULT_PATH)

        raise FileNotFoundError("No configuration file found")

    def _find_project_config(self) -> Optional[Path]:
        """
        Search for project-level configuration file.

        Searches current directory and parent directories up to git root.

        Returns:
            Path to project config or None
        """
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
            if parent == current:  # Reached filesystem root
                break
            current = parent

        return None

    def init_project_config(
        self,
        template: str = 'default-secure',
        force: bool = False
    ) -> Path:
        """
        Initialize project-level configuration.

        Creates .ai-governance/policy.yaml in current directory.

        Args:
            template: Template to use (default-secure, permissive, strict)
            force: Overwrite existing config

        Returns:
            Path to created config file
        """
        # Determine output path
        output_dir = self.project_root / '.ai-governance'
        output_file = output_dir / 'policy.yaml'

        # Check if already exists
        if output_file.exists() and not force:
            click.echo(f"{Fore.YELLOW}✗ Config already exists: {output_file}{Style.RESET_ALL}")
            click.echo(f"  Use --force to overwrite")
            return output_file

        # Create directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get template source
        template_path = self._get_template_path(template)

        # Copy template
        shutil.copy2(template_path, output_file)

        click.echo(f"{Fore.GREEN}✓ Created project config: {output_file}{Style.RESET_ALL}")
        click.echo(f"  Template: {template}")
        click.echo(f"\n  Edit this file to customize security rules for your project.")
        click.echo(f"  This file will be used automatically when running ai-governance commands.")

        # Create .gitignore entry suggestion
        self._suggest_gitignore(output_dir)

        return output_file

    def init_user_config(
        self,
        template: str = 'default-secure',
        force: bool = False
    ) -> Path:
        """
        Initialize user-level configuration.

        Creates ~/.config/ai-governance/policy.yaml

        Args:
            template: Template to use
            force: Overwrite existing config

        Returns:
            Path to created config file
        """
        output_file = self.USER_CONFIG_PATH

        # Check if already exists
        if output_file.exists() and not force:
            click.echo(f"{Fore.YELLOW}✗ User config already exists: {output_file}{Style.RESET_ALL}")
            click.echo(f"  Use --force to overwrite")
            return output_file

        # Create directory
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Get template source
        template_path = self._get_template_path(template)

        # Copy template
        shutil.copy2(template_path, output_file)

        click.echo(f"{Fore.GREEN}✓ Created user config: {output_file}{Style.RESET_ALL}")
        click.echo(f"  Template: {template}")
        click.echo(f"\n  This config will be used as default for all projects.")
        click.echo(f"  Project-level configs will override these settings.")

        return output_file

    def _get_template_path(self, template: str) -> Path:
        """
        Get path to template file.

        Args:
            template: Template name

        Returns:
            Path to template file
        """
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

    def _suggest_gitignore(self, config_dir: Path):
        """
        Suggest adding config directory to .gitignore.

        Args:
            config_dir: Configuration directory path
        """
        gitignore_path = self.project_root / '.gitignore'

        # Check if .gitignore exists
        if not gitignore_path.exists():
            click.echo(f"\n  {Fore.YELLOW}Tip:{Style.RESET_ALL} Create a .gitignore file to exclude sensitive configs:")
            click.echo(f"    echo '.ai-governance/secrets.yaml' >> .gitignore")
            return

        # Check if already ignored
        try:
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()

            if '.ai-governance' not in gitignore_content:
                click.echo(f"\n  {Fore.YELLOW}Tip:{Style.RESET_ALL} Consider adding to .gitignore:")
                click.echo(f"    echo '.ai-governance/secrets.yaml' >> .gitignore")
        except Exception:
            pass

    def list_configs(self) -> Dict[str, Optional[str]]:
        """
        List all discovered configuration files.

        Returns:
            Dict with config level and path
        """
        configs = {}

        # Project-level
        project_config = self._find_project_config()
        configs['project'] = str(project_config) if project_config else None

        # User-level
        configs['user'] = str(self.USER_CONFIG_PATH) if self.USER_CONFIG_PATH.exists() else None

        # System-level
        configs['system'] = str(self.SYSTEM_DEFAULT_PATH) if self.SYSTEM_DEFAULT_PATH.exists() else None

        return configs

    def show_config_status(self):
        """Display current configuration status."""
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Configuration Status{Style.RESET_ALL}")
        click.echo(f"{'='*70}\n")

        configs = self.list_configs()

        # Project-level
        if configs['project']:
            click.echo(f"  {Fore.GREEN}✓{Style.RESET_ALL} Project config: {configs['project']}")
        else:
            click.echo(f"  {Fore.YELLOW}○{Style.RESET_ALL} Project config: Not found")
            click.echo(f"    {Fore.DIM}Run: ai-governance init --project{Style.RESET_ALL}")

        # User-level
        if configs['user']:
            click.echo(f"  {Fore.GREEN}✓{Style.RESET_ALL} User config:    {configs['user']}")
        else:
            click.echo(f"  {Fore.YELLOW}○{Style.RESET_ALL} User config:    Not found")
            click.echo(f"    {Fore.DIM}Run: ai-governance init --user{Style.RESET_ALL}")

        # System-level
        if configs['system']:
            click.echo(f"  {Fore.GREEN}✓{Style.RESET_ALL} System default: {configs['system']}")

        # Active config
        click.echo(f"\n{Fore.YELLOW}Active Config:{Style.RESET_ALL}")
        try:
            active = self.find_config()
            click.echo(f"  → {active}")
        except FileNotFoundError as e:
            click.echo(f"  {Fore.RED}✗ {e}{Style.RESET_ALL}")

        click.echo()

    def create_template_files(self):
        """Create additional template files if they don't exist."""
        templates_dir = Path(__file__).parent / 'profiles'
        templates_dir.mkdir(exist_ok=True)

        # Permissive template
        permissive_path = templates_dir / 'permissive.yaml'
        if not permissive_path.exists():
            self._create_permissive_template(permissive_path)

        # Strict template
        strict_path = templates_dir / 'strict.yaml'
        if not strict_path.exists():
            self._create_strict_template(strict_path)

    def _create_permissive_template(self, path: Path):
        """Create a permissive security template."""
        content = """# AI Governance - Permissive Security Policy
# This template has relaxed security rules for development environments

security:
  # Allowed file patterns (minimal restrictions)
  allowed_patterns:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.jsx"
    - "**/*.tsx"
    - "**/*.java"
    - "**/*.go"
    - "**/*.rs"
    - "**/*.rb"
    - "**/*.php"

  # Blocked patterns (only critical files)
  blocked_patterns:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"
    - "**/__pycache__/**"

  # Sensitive content detection (reduced)
  detect_secrets:
    enabled: true
    patterns:
      # Only detect obvious secrets
      - 'sk-[a-zA-Z0-9]{32,}'  # OpenAI API keys
      - 'AKIA[0-9A-Z]{16}'      # AWS Access Keys

  # Size limits
  max_file_size: 1048576  # 1MB
"""
        with open(path, 'w') as f:
            f.write(content)

    def _create_strict_template(self, path: Path):
        """Create a strict security template."""
        content = """# AI Governance - Strict Security Policy
# This template has enhanced security rules for production environments

security:
  # Very restrictive allowed patterns
  allowed_patterns:
    - "src/**/*.py"
    - "src/**/*.js"
    - "lib/**/*.py"
    - "app/**/*.js"

  # Extensive blocked patterns
  blocked_patterns:
    - "**/test/**"
    - "**/tests/**"
    - "**/*_test.py"
    - "**/config/**"
    - "**/secrets/**"
    - "**/.env*"
    - "**/credentials/**"
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"
    - "**/__pycache__/**"
    - "**/build/**"
    - "**/dist/**"

  # Enhanced secret detection
  detect_secrets:
    enabled: true
    patterns:
      # API Keys
      - 'api[_-]?key[_-]?=.{8,}'
      - 'sk-[a-zA-Z0-9]{32,}'
      - 'AKIA[0-9A-Z]{16}'

      # Passwords
      - 'password[_-]?=.{4,}'
      - 'passwd[_-]?=.{4,}'
      - 'pwd[_-]?=.{4,}'

      # Tokens
      - 'token[_-]?=.{8,}'
      - 'auth[_-]?=.{8,}'
      - 'bearer[_-]+[a-zA-Z0-9_\-\.=]+'

      # Private keys
      - '-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----'

      # Database URLs
      - 'postgres://[^:]+:[^@]+@'
      - 'mysql://[^:]+:[^@]+@'

      # AWS
      - 'aws_secret_access_key'
      - 'aws_session_token'

  # Strict size limits
  max_file_size: 524288  # 512KB
"""
        with open(path, 'w') as f:
            f.write(content)
