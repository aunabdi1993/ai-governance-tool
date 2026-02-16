"""Command-line interface for AI Governance Tool."""

import click
import os
from pathlib import Path
from colorama import Fore, Style, init
from dotenv import load_dotenv

from .policy_engine import PolicyEngine
from .scanner import Scanner
from .ai_client import AIClient
from .diff_manager import DiffManager
from .audit_logger import AuditLogger
from .file_discoverer import FileDiscoverer
from .batch_processor import BatchProcessor
from .codebase_refactor import CodebaseRefactor
from .language_config import (
    get_extensions_for_languages,
    parse_extensions,
    get_supported_languages,
    get_all_extensions
)

# Initialize colorama
init(autoreset=True)

# Load environment variables from current directory only
# This allows users to optionally set API keys via .env files
# but the tool itself never creates these files for security
load_dotenv()


def ensure_api_key() -> bool:
    """Ensure API key is configured. Prompt user if not found.

    Returns:
        True if API key is available, False otherwise
    """
    # Check if API key is already set
    if os.getenv('ANTHROPIC_API_KEY') and os.getenv('ANTHROPIC_API_KEY') != 'your_api_key_here':
        return True

    # API key not found, prompt user
    click.echo(f"\n{Fore.YELLOW}⚠️  Anthropic API key not found{Style.RESET_ALL}\n")
    click.echo("To use AI refactoring, you need an Anthropic API key.")
    click.echo("Get your key from: https://console.anthropic.com/\n")

    # Ask if they want to configure it now
    if not click.confirm("Would you like to configure it now?", default=True):
        click.echo(f"\n{Fore.CYAN}You can configure it later by running:{Style.RESET_ALL}")
        click.echo("  ai-governance init\n")
        return False

    # Prompt for API key (hide input for security)
    api_key = click.prompt(
        f"\n{Fore.CYAN}Enter your Anthropic API key{Style.RESET_ALL}",
        hide_input=True,
        type=str
    ).strip()

    # Basic validation
    if not api_key or api_key == 'your_api_key_here':
        click.echo(f"\n{Fore.RED}Invalid API key provided{Style.RESET_ALL}")
        return False

    # Set it for current session only (more secure)
    os.environ['ANTHROPIC_API_KEY'] = api_key

    click.echo(f"\n{Fore.GREEN}✅ API key set for this session{Style.RESET_ALL}")
    click.echo(f"{Fore.YELLOW}Note: For security, the key is NOT saved to disk.{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}You'll be prompted again in the next session.{Style.RESET_ALL}\n")

    # Show how to set it permanently via environment if they want
    click.echo(f"{Fore.DIM}Tip: To avoid re-entering, set environment variable:{Style.RESET_ALL}")
    click.echo(f"{Fore.DIM}  export ANTHROPIC_API_KEY='your_key_here'{Style.RESET_ALL}\n")

    return True


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AI Governance Tool - Secure AI-assisted code refactoring with policy controls.

    This tool demonstrates how to safely use AI for code refactoring by:
    - Scanning files for sensitive content before sending to AI
    - Blocking files that match security policies
    - Logging all actions for audit purposes
    - Showing diffs and tracking costs
    """
    pass


@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option(
    '--target',
    '-t',
    required=True,
    help='Description of desired refactoring (e.g., "refactor to async/await patterns")'
)
@click.option(
    '--policy',
    '-p',
    type=click.Path(exists=True),
    help='Path to policy YAML file (default: profiles/default-secure.yaml)'
)
@click.option(
    '--no-backup',
    is_flag=True,
    help='Do not create backup file'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Scan only, do not refactor'
)
@click.option(
    '--apply',
    is_flag=True,
    help='Automatically apply refactored code without confirmation'
)
def refactor(filepath, target, policy, no_backup, dry_run, apply):
    """Refactor a file using AI with security controls.

    Example:
        ai-governance refactor demo/legacy_code/utils.py --target "modernize to Python 3.10+"
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Refactor{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    # Initialize components
    try:
        policy_engine = PolicyEngine(policy)
        scanner = Scanner(policy_engine)
        audit_logger = AuditLogger()
        diff_manager = DiffManager(create_backups=not no_backup)
    except Exception as e:
        click.echo(f"{Fore.RED}Error initializing components: {e}{Style.RESET_ALL}")
        return

    # Show policy info
    policy_info = policy_engine.get_policy_info()
    click.echo(f"{Fore.YELLOW}Policy: {policy_info['name']} (v{policy_info['version']}){Style.RESET_ALL}")
    click.echo(f"Description: {policy_info['description']}\n")

    # Scan file
    click.echo(f"{Fore.CYAN}Scanning file: {filepath}{Style.RESET_ALL}")
    scan_result = scanner.scan_file(filepath)

    # Display scan results
    if scan_result.get('error'):
        click.echo(f"\n{Fore.RED}❌ ERROR: {scan_result['reason']}{Style.RESET_ALL}")
        audit_logger.log_action(
            filepath=filepath,
            action='refactor',
            status='error',
            reason=scan_result['reason']
        )
        return

    if not scan_result['allowed']:
        click.echo(f"\n{Fore.RED}🚫 BLOCKED: {scan_result['reason']}{Style.RESET_ALL}")
        click.echo(f"File size: {scan_result['file_size']} bytes\n")

        if scan_result['findings']:
            click.echo(f"{Fore.YELLOW}Sensitive patterns detected:{Style.RESET_ALL}")
            for finding in scan_result['findings']:
                click.echo(f"  • {Fore.RED}{finding['pattern']}{Style.RESET_ALL} "
                          f"({finding['severity']}): {finding['description']}")
                click.echo(f"    Matches: {finding['match_count']}, "
                          f"Examples: {', '.join(finding['examples'])}")

        # Log blocked attempt
        audit_logger.log_action(
            filepath=filepath,
            action='refactor',
            status='blocked',
            reason=scan_result['reason'],
            findings=scan_result['findings'],
            target_description=target
        )

        click.echo(f"\n{Fore.YELLOW}⚠️  File blocked by security policy. Not sent to AI.{Style.RESET_ALL}")
        return

    # File passed security checks
    click.echo(f"\n{Fore.GREEN}✅ PASSED: {scan_result['reason']}{Style.RESET_ALL}")
    click.echo(f"File size: {scan_result['file_size']} bytes")

    if dry_run:
        click.echo(f"\n{Fore.YELLOW}Dry run mode - stopping before refactoring{Style.RESET_ALL}")
        audit_logger.log_action(
            filepath=filepath,
            action='scan',
            status='allowed',
            reason=scan_result['reason']
        )
        return

    # Ensure API key is configured before making AI calls
    if not ensure_api_key():
        click.echo(f"\n{Fore.RED}Cannot proceed without API key{Style.RESET_ALL}")
        return

    # Refactor with AI
    click.echo(f"\n{Fore.CYAN}Refactoring with AI...{Style.RESET_ALL}")
    click.echo(f"Target: {target}")

    try:
        ai_client = AIClient()
        click.echo(f"Model: {ai_client.model}\n")

        # Estimate cost first
        estimate = ai_client.estimate_cost(scan_result['content'], target)
        click.echo(f"{Fore.YELLOW}Estimated cost: ${estimate['estimated_cost']:.4f}{Style.RESET_ALL}")
        click.echo(f"Estimated tokens: ~{estimate['estimated_total_tokens']}\n")

        # Call AI
        result = ai_client.refactor_code(
            code=scan_result['content'],
            target_description=target,
            filepath=filepath
        )

        if not result['success']:
            click.echo(f"{Fore.RED}Error during refactoring: {result['error']}{Style.RESET_ALL}")
            audit_logger.log_action(
                filepath=filepath,
                action='refactor',
                status='error',
                reason=result['error'],
                target_description=target,
                model=result['model']
            )
            return

        # Display results
        click.echo(f"{Fore.GREEN}✅ Refactoring completed!{Style.RESET_ALL}\n")
        click.echo(f"{Fore.YELLOW}Tokens used: {result['tokens_used']['total']}{Style.RESET_ALL}")
        click.echo(f"  Input:  {result['tokens_used']['input']}")
        click.echo(f"  Output: {result['tokens_used']['output']}")
        click.echo(f"{Fore.YELLOW}Actual cost: ${result['cost']:.6f}{Style.RESET_ALL}\n")

        # Show diff
        diff_manager.display_diff(
            original=scan_result['content'],
            refactored=result['refactored_code'],
            filepath=filepath
        )

        # Show stats
        stats = diff_manager.get_stats(scan_result['content'], result['refactored_code'])
        diff_manager.display_stats(stats)

        # Log success
        audit_logger.log_action(
            filepath=filepath,
            action='refactor',
            status='success',
            reason='Refactoring completed successfully',
            tokens_used=result['tokens_used']['total'],
            cost=result['cost'],
            model=result['model'],
            target_description=target,
            original_code=scan_result['content'],
            refactored_code=result['refactored_code']
        )

        # Ask to apply changes (unless --apply flag is set)
        if apply or click.confirm(f"\n{Fore.CYAN}Apply changes to {filepath}?{Style.RESET_ALL}"):
            # Create backup
            if not no_backup:
                backup_path = diff_manager.create_backup(filepath)
                if backup_path:
                    click.echo(f"{Fore.GREEN}Backup created: {backup_path}{Style.RESET_ALL}")

            # Save refactored code
            if diff_manager.save_refactored(filepath, result['refactored_code']):
                click.echo(f"{Fore.GREEN}✅ Changes applied to {filepath}{Style.RESET_ALL}")
            else:
                click.echo(f"{Fore.RED}❌ Failed to save changes{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.YELLOW}Changes not applied{Style.RESET_ALL}")

    except ValueError as e:
        click.echo(f"\n{Fore.RED}Configuration error: {e}{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}Set ANTHROPIC_API_KEY environment variable{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('paths', nargs=-1, required=True, type=click.Path())
@click.option(
    '--target',
    '-t',
    help='Description of desired refactoring (e.g., "refactor to async/await patterns")'
)
@click.option(
    '--policy',
    '-p',
    type=click.Path(exists=True),
    help='Path to policy YAML file (default: profiles/default-secure.yaml)'
)
@click.option(
    '--no-backup',
    is_flag=True,
    help='Do not create backup files'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Scan only, do not refactor'
)
@click.option(
    '--apply',
    is_flag=True,
    help='Automatically apply refactored code without confirmation'
)
@click.option(
    '--recursive/--no-recursive',
    default=True,
    help='Recursively search directories (default: enabled)'
)
@click.option(
    '--pattern',
    help='File pattern to match (e.g., "test_*.py", "*.js")'
)
@click.option(
    '--lang',
    '--language',
    'languages',
    multiple=True,
    help='Programming language(s) to process (e.g., python, javascript, typescript). Can specify multiple times.'
)
@click.option(
    '--ext',
    '--extensions',
    'extensions',
    help='Comma-separated file extensions (e.g., "py,js,ts" or ".py,.js,.ts"). Overrides --lang.'
)
@click.option(
    '--list-languages',
    is_flag=True,
    help='List all supported languages and exit'
)
def bulk_refactor(paths, target, policy, no_backup, dry_run, apply, recursive, pattern,
                  languages, extensions, list_languages):
    """Refactor multiple files or entire directories using AI.

    Supports all common programming languages (Python, JavaScript, TypeScript, Java, C++, Go, Rust, etc.)

    PATHS can be:
    - Multiple files: ai-governance bulk-refactor file1.py file2.js --target "..."
    - Directories: ai-governance bulk-refactor src/ tests/ --target "..."
    - Mix of both: ai-governance bulk-refactor file.py src/ --target "..."

    Examples:
        # Refactor all supported files in a directory
        ai-governance bulk-refactor src/ --target "modernize code"

        # Refactor only Python files
        ai-governance bulk-refactor src/ --lang python --target "add type hints"

        # Refactor JavaScript and TypeScript files
        ai-governance bulk-refactor src/ --lang javascript --lang typescript --target "convert to ES6+"

        # Refactor specific file extensions
        ai-governance bulk-refactor src/ --ext "js,jsx,ts,tsx" --target "refactor to hooks"

        # Refactor files matching a pattern
        ai-governance bulk-refactor tests/ --pattern "test_*.py" --target "use pytest fixtures"

        # List all supported languages
        ai-governance bulk-refactor . --list-languages

        # Dry run to see what would be refactored
        ai-governance bulk-refactor src/ --target "..." --dry-run

        # Auto-apply changes without confirmation
        ai-governance bulk-refactor src/ --target "..." --apply
    """
    # Handle --list-languages flag
    if list_languages:
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Supported Programming Languages{Style.RESET_ALL}")
        click.echo(f"{'=' * 70}\n")
        supported_langs = get_supported_languages()

        # Display in columns
        from .language_config import LANGUAGE_EXTENSIONS
        for i, lang in enumerate(supported_langs, 1):
            exts = ', '.join(sorted(LANGUAGE_EXTENSIONS[lang]))
            click.echo(f"{i:2}. {lang:15} - {exts}")

        click.echo(f"\n{Fore.YELLOW}Usage:{Style.RESET_ALL}")
        click.echo(f"  --lang python              (refactor Python files)")
        click.echo(f"  --lang python --lang java  (refactor Python and Java)")
        click.echo(f"  --ext py,js,ts             (refactor specific extensions)")
        click.echo()
        return

    # Validate that --target is provided
    if not target:
        click.echo(f"{Fore.RED}Error: --target/-t is required{Style.RESET_ALL}")
        click.echo(f"\nUsage: ai-governance bulk-refactor PATHS --target \"description\"")
        click.echo(f"       ai-governance bulk-refactor --list-languages")
        return

    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Bulk Refactor{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    # Initialize components
    try:
        policy_engine = PolicyEngine(policy)
        scanner = Scanner(policy_engine)
        audit_logger = AuditLogger()
        diff_manager = DiffManager(create_backups=not no_backup)
    except Exception as e:
        click.echo(f"{Fore.RED}Error initializing components: {e}{Style.RESET_ALL}")
        return

    # Show policy info
    policy_info = policy_engine.get_policy_info()
    click.echo(f"{Fore.YELLOW}Policy: {policy_info['name']} (v{policy_info['version']}){Style.RESET_ALL}")
    click.echo(f"Description: {policy_info['description']}\n")

    # Determine file extensions to process
    supported_extensions = None
    if extensions:
        # User specified custom extensions
        supported_extensions = parse_extensions(extensions)
        click.echo(f"{Fore.CYAN}File extensions: {', '.join(sorted(supported_extensions))}{Style.RESET_ALL}")
    elif languages:
        # User specified languages
        try:
            supported_extensions = get_extensions_for_languages(list(languages))
            click.echo(f"{Fore.CYAN}Languages: {', '.join(languages)}{Style.RESET_ALL}")
            click.echo(f"File extensions: {', '.join(sorted(supported_extensions))}{Style.RESET_ALL}")
        except ValueError as e:
            click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            click.echo(f"\n{Fore.YELLOW}Use --list-languages to see supported languages{Style.RESET_ALL}")
            return
    else:
        # No language or extension specified - use all supported languages
        supported_extensions = get_all_extensions()
        click.echo(f"{Fore.CYAN}Processing all supported file types{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}Tip: Use --lang or --ext to filter specific languages{Style.RESET_ALL}")

    # Discover files
    click.echo(f"\n{Fore.CYAN}Discovering files...{Style.RESET_ALL}")
    discoverer = FileDiscoverer(supported_extensions=supported_extensions)
    files = discoverer.discover_files(
        paths=list(paths),
        recursive=recursive,
        pattern=pattern
    )

    if not files:
        click.echo(f"{Fore.YELLOW}No files found matching criteria{Style.RESET_ALL}")
        return

    click.echo(f"Found {len(files)} file(s) to process:\n")
    for file_path in files:
        click.echo(f"  • {file_path}")

    # Confirm before proceeding (unless --apply or --dry-run)
    if not dry_run and not apply:
        click.echo(f"\n{Fore.YELLOW}This will refactor {len(files)} file(s) using AI.{Style.RESET_ALL}")
        if not click.confirm("Do you want to continue?", default=True):
            click.echo(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return

    # Ensure API key is configured before making AI calls
    if not dry_run and not ensure_api_key():
        click.echo(f"\n{Fore.RED}Cannot proceed without API key{Style.RESET_ALL}")
        return

    # Initialize AI client if not dry run
    ai_client = None
    if not dry_run:
        try:
            ai_client = AIClient()
            click.echo(f"\n{Fore.CYAN}Model: {ai_client.model}{Style.RESET_ALL}")
        except Exception as e:
            click.echo(f"{Fore.RED}Error initializing AI client: {e}{Style.RESET_ALL}")
            return

    # Process files
    click.echo(f"\n{Fore.CYAN}Processing files...{Style.RESET_ALL}")
    batch_processor = BatchProcessor(
        policy_engine=policy_engine,
        scanner=scanner,
        ai_client=ai_client,
        diff_manager=diff_manager,
        audit_logger=audit_logger,
        no_backup=no_backup,
        dry_run=dry_run,
        apply=apply
    )

    batch_result = batch_processor.process_files(
        files=files,
        target=target,
        show_progress=True
    )

    # Display summary
    click.echo(batch_result.get_summary())

    # Show detailed results for failed/blocked files
    if batch_result.blocked > 0:
        click.echo(f"{Fore.YELLOW}Blocked files:{Style.RESET_ALL}")
        for filepath, result in batch_result.file_results.items():
            if result['status'] == 'blocked':
                click.echo(f"  • {filepath}: {result['reason']}")
        click.echo()

    if batch_result.failed > 0:
        click.echo(f"{Fore.RED}Failed files:{Style.RESET_ALL}")
        for filepath, result in batch_result.file_results.items():
            if result['status'] == 'failed':
                click.echo(f"  • {filepath}: {result['reason']}")
        click.echo()


@cli.command()
@click.argument('paths', nargs=-1, required=True, type=click.Path())
@click.option(
    '--target',
    '-t',
    required=True,
    help='Description of desired refactoring (e.g., "refactor to async/await patterns")'
)
@click.option(
    '--policy',
    '-p',
    type=click.Path(exists=True),
    help='Path to policy YAML file (default: profiles/default-secure.yaml)'
)
@click.option(
    '--no-backup',
    is_flag=True,
    help='Do not create backup files'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Scan and analyze, but do not apply changes'
)
@click.option(
    '--no-validation',
    is_flag=True,
    help='Disable cross-file validation'
)
@click.option(
    '--enable-type-checking',
    is_flag=True,
    help='Enable external type checkers (mypy, tsc)'
)
@click.option(
    '--enable-testing',
    is_flag=True,
    help='Run tests to validate refactored code'
)
@click.option(
    '--no-impact-analysis',
    is_flag=True,
    help='Disable change impact analysis'
)
@click.option(
    '--no-resume',
    is_flag=True,
    help='Disable checkpoint/resume functionality'
)
@click.option(
    '--resume',
    'resume_session',
    help='Resume from a previous session (provide session ID)'
)
@click.option(
    '--no-plan',
    is_flag=True,
    help='Skip displaying refactoring plan'
)
@click.option(
    '--recursive/--no-recursive',
    default=True,
    help='Recursively search directories (default: enabled)'
)
@click.option(
    '--pattern',
    help='File pattern to match (e.g., "test_*.py", "*.js")'
)
@click.option(
    '--lang',
    '--language',
    'languages',
    multiple=True,
    help='Programming language(s) to process (e.g., python, javascript, typescript). Can specify multiple times.'
)
@click.option(
    '--ext',
    '--extensions',
    'extensions',
    help='Comma-separated file extensions (e.g., "py,js,ts" or ".py,.js,.ts"). Overrides --lang.'
)
def codebase_refactor(paths, target, policy, no_backup, dry_run, no_validation,
                      enable_type_checking, enable_testing, no_impact_analysis,
                      no_resume, resume_session, no_plan, recursive, pattern, languages, extensions):
    """Refactor entire codebase with dependency awareness (ENHANCED).

    This advanced command provides intelligent, context-aware refactoring with:
    - 🔍 Call graph analysis to understand function relationships
    - 🎯 Smart context selection for better AI understanding
    - 📋 Refactoring plan generation and review
    - ✅ Test-driven validation (runs your test suite)
    - 📊 Change impact analysis (risk assessment)
    - 💾 Checkpoint/resume for large codebases
    - 🔐 Cross-file validation for breaking changes

    PATHS can be:
    - Multiple files: ai-governance codebase-refactor file1.py file2.py --target "..."
    - Directories: ai-governance codebase-refactor src/ --target "..."
    - Mix of both: ai-governance codebase-refactor file.py src/ --target "..."

    Examples:
        # Full-featured refactoring with all validations
        ai-governance codebase-refactor src/ --target "modernize to Python 3.12" \\
          --enable-testing --enable-type-checking

        # Refactor with impact analysis
        ai-governance codebase-refactor src/ --target "add async/await"

        # Resume interrupted session
        ai-governance codebase-refactor --resume refactor_20250216_143022_abc123 \\
          --target "modernize code"

        # Dry run to preview changes and plan
        ai-governance codebase-refactor src/ --target "refactor classes" --dry-run

        # Quick exploratory refactoring (skip validations)
        ai-governance codebase-refactor src/ --target "experiment" \\
          --no-validation --no-impact-analysis --no-plan
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Codebase Refactor{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    # Determine file extensions to process
    supported_extensions = None
    if extensions:
        supported_extensions = parse_extensions(extensions)
        click.echo(f"{Fore.CYAN}File extensions: {', '.join(sorted(supported_extensions))}{Style.RESET_ALL}")
    elif languages:
        try:
            supported_extensions = get_extensions_for_languages(list(languages))
            click.echo(f"{Fore.CYAN}Languages: {', '.join(languages)}{Style.RESET_ALL}")
        except ValueError as e:
            click.echo(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            return
    else:
        # Default to all supported languages
        supported_extensions = get_all_extensions()
        click.echo(f"{Fore.CYAN}Processing all supported file types{Style.RESET_ALL}")

    # Discover files
    click.echo(f"{Fore.CYAN}Discovering files...{Style.RESET_ALL}")
    discoverer = FileDiscoverer(supported_extensions=supported_extensions)
    files = discoverer.discover_files(
        paths=list(paths),
        recursive=recursive,
        pattern=pattern
    )

    if not files:
        click.echo(f"{Fore.YELLOW}No files found matching criteria{Style.RESET_ALL}")
        return

    # Confirm before proceeding
    if not dry_run:
        click.echo(f"\n{Fore.YELLOW}This will refactor {len(files)} file(s) with dependency awareness.{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}Files will be analyzed for dependencies and refactored in groups.{Style.RESET_ALL}")

        if not click.confirm("\nDo you want to continue?", default=True):
            click.echo(f"{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            return

    # Ensure API key is configured
    if not dry_run and not ensure_api_key():
        click.echo(f"\n{Fore.RED}Cannot proceed without API key{Style.RESET_ALL}")
        return

    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key and not dry_run:
        click.echo(f"{Fore.RED}API key not found{Style.RESET_ALL}")
        return

    # Initialize codebase refactor orchestrator
    policy_path = policy or "ai_governance/profiles/default-secure.yaml"

    try:
        refactorer = CodebaseRefactor(
            api_key=api_key,
            policy_path=policy_path,
            enable_validation=not no_validation,
            enable_type_checking=enable_type_checking,
            enable_testing=enable_testing,
            enable_impact_analysis=not no_impact_analysis,
            enable_resume=not no_resume,
            show_plan=not no_plan
        )

        # Run codebase refactoring
        summary = refactorer.refactor_codebase(
            file_paths=files,
            target=target,
            dry_run=dry_run,
            create_backup=not no_backup,
            resume_session=resume_session
        )

        # Show final message
        if summary['successful'] == summary['total_files']:
            click.echo(f"{Fore.GREEN}✅ All files refactored successfully!{Style.RESET_ALL}")
        elif summary['successful'] > 0:
            click.echo(f"{Fore.YELLOW}⚠️  Partial success - some files failed{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.RED}✗ Refactoring failed{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"\n{Fore.RED}Error during codebase refactoring: {e}{Style.RESET_ALL}")
        import traceback
        if '--debug' in os.sys.argv:
            traceback.print_exc()


@cli.command()
def init():
    """Initialize AI Governance configuration.

    Creates configuration file for global or project-specific use.
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Initialization{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    click.echo("Welcome to AI Governance Tool!")
    click.echo("This tool helps you safely refactor code using AI with security controls.\n")

    # Check if API key already exists
    existing_key = os.getenv('ANTHROPIC_API_KEY')
    if existing_key and existing_key != 'your_api_key_here':
        click.echo(f"{Fore.GREEN}✅ API key already configured{Style.RESET_ALL}\n")
        reconfigure = click.confirm("Would you like to reconfigure it?", default=False)
        if not reconfigure:
            click.echo(f"\n{Fore.CYAN}Configuration unchanged. You're ready to go!{Style.RESET_ALL}")
            click.echo(f"\nTry: ai-governance refactor <file> --target \"<description>\"\n")
            return

    # Prompt for API key
    click.echo(f"{Fore.YELLOW}Step 1: API Key Configuration{Style.RESET_ALL}")
    click.echo("You'll need an Anthropic API key to use AI refactoring.")
    click.echo("Get your key from: https://console.anthropic.com/\n")

    has_key = click.confirm("Do you have your API key ready?", default=True)

    if not has_key:
        click.echo(f"\n{Fore.CYAN}No problem! You can configure it later.{Style.RESET_ALL}")
        click.echo("When you're ready, run this command again: ai-governance init\n")
        click.echo("You can also configure it on your first refactor command.\n")
        return

    # Get API key from user
    api_key = click.prompt(
        f"\n{Fore.CYAN}Enter your Anthropic API key{Style.RESET_ALL}",
        hide_input=True,
        type=str
    ).strip()

    # Basic validation
    if not api_key or api_key == 'your_api_key_here':
        click.echo(f"\n{Fore.RED}Invalid API key provided{Style.RESET_ALL}")
        click.echo("Please run this command again when you have a valid API key.\n")
        return

    # Verify the key works by setting it temporarily
    os.environ['ANTHROPIC_API_KEY'] = api_key

    click.echo(f"\n{Fore.GREEN}✅ API key validated!{Style.RESET_ALL}\n")

    # Explain the security model
    click.echo(f"{Fore.YELLOW}Security Note:{Style.RESET_ALL}")
    click.echo("For security, API keys are NOT saved to disk by this tool.")
    click.echo("You'll be prompted to enter your key when starting each session.\n")

    click.echo(f"{Fore.CYAN}If you prefer to set it permanently, add this to your shell profile:{Style.RESET_ALL}")
    click.echo(f"  export ANTHROPIC_API_KEY='{api_key[:10]}...'\n")

    click.echo(f"{Fore.CYAN}Shell profile locations:{Style.RESET_ALL}")
    click.echo("  Bash: ~/.bashrc or ~/.bash_profile")
    click.echo("  Zsh:  ~/.zshrc")
    click.echo("  Fish: ~/.config/fish/config.fish\n")

    # Show success message and next steps
    click.echo(f"{Fore.GREEN}🎉 Setup complete! You're ready to use AI Governance Tool.{Style.RESET_ALL}\n")

    click.echo(f"{Fore.CYAN}Try it out:{Style.RESET_ALL}")
    click.echo("  ai-governance refactor <file> --target \"modernize code\"")
    click.echo("  ai-governance refactor <file> --target \"add comments\" --dry-run")
    click.echo("  ai-governance audit\n")

    click.echo(f"{Fore.CYAN}Features:{Style.RESET_ALL}")
    click.echo("  • Security scanning - Blocks files with sensitive data")
    click.echo("  • Audit logging - Tracks all actions in .ai-governance-audit.db")
    click.echo("  • Cost tracking - Shows estimated costs before API calls")
    click.echo("  • Policy controls - Customizable with --policy <path-to-yaml>\n")


@cli.command()
@click.option(
    '--limit',
    '-l',
    default=50,
    help='Number of recent logs to show'
)
@click.option(
    '--status',
    '-s',
    type=click.Choice(['allowed', 'blocked', 'error', 'success']),
    help='Filter by status'
)
@click.option(
    '--stats',
    is_flag=True,
    help='Show statistics only'
)
def audit(limit, status, stats):
    """View audit logs and statistics.

    Examples:
        ai-governance audit
        ai-governance audit --status blocked
        ai-governance audit --stats
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Audit Logs{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    try:
        audit_logger = AuditLogger()

        # Show statistics
        if stats:
            statistics = audit_logger.get_statistics()
            click.echo(f"{Fore.YELLOW}{Style.BRIGHT}Audit Statistics:{Style.RESET_ALL}\n")
            click.echo(f"Total requests: {statistics['total_requests']}")
            click.echo(f"Total tokens:   {statistics['total_tokens']}")
            click.echo(f"Total cost:     ${statistics['total_cost']:.4f}")
            click.echo(f"Recent (24h):   {statistics['recent_24h']}\n")

            click.echo(f"{Fore.YELLOW}Status Breakdown:{Style.RESET_ALL}")
            for status_name, count in statistics['status_counts'].items():
                click.echo(f"  {status_name}: {count}")
            return

        # Get logs
        if status:
            logs = audit_logger.get_logs_by_status(status, limit)
            click.echo(f"{Fore.YELLOW}Showing {len(logs)} logs with status: {status}{Style.RESET_ALL}")
        else:
            logs = audit_logger.get_recent_logs(limit)
            click.echo(f"{Fore.YELLOW}Showing {len(logs)} most recent logs{Style.RESET_ALL}")

        # Display logs
        for log_entry in logs:
            formatted = audit_logger.format_log_entry(log_entry)
            click.echo(formatted)

        if not logs:
            click.echo(f"\n{Fore.YELLOW}No audit logs found{Style.RESET_ALL}")

    except Exception as e:
        click.echo(f"{Fore.RED}Error reading audit logs: {e}{Style.RESET_ALL}")


@cli.command()
@click.option(
    '--list',
    'list_sessions',
    is_flag=True,
    help='List all saved refactoring sessions'
)
@click.option(
    '--resume',
    'session_id',
    help='Resume a specific session by ID'
)
@click.option(
    '--delete',
    'delete_session',
    help='Delete a specific session by ID'
)
@click.option(
    '--clean',
    'clean_days',
    type=int,
    help='Delete sessions older than specified days'
)
def sessions(list_sessions, session_id, delete_session, clean_days):
    """Manage refactoring sessions (list, resume, delete).

    Examples:
        ai-governance sessions --list
        ai-governance sessions --resume refactor_20250216_143022_abc123
        ai-governance sessions --delete refactor_20250216_143022_abc123
        ai-governance sessions --clean 30
    """
    from .refactor_state import RefactorState

    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Session Management{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    state_manager = RefactorState()

    if list_sessions:
        state_manager.display_sessions()

    elif session_id:
        # Resume session
        if not state_manager.can_resume(session_id):
            click.echo(f"{Fore.RED}Session {session_id} not found or has no pending files{Style.RESET_ALL}")
            return

        resume_info = state_manager.get_resume_info(session_id)
        click.echo(f"{Fore.CYAN}Session: {session_id}{Style.RESET_ALL}")
        click.echo(f"Target: {resume_info.get('target', 'Unknown')}")
        click.echo(f"Pending files: {len(resume_info.get('pending_files', []))}")
        click.echo()

        if click.confirm("Resume this session?", default=True):
            # User should use codebase-refactor --resume instead
            click.echo(f"\n{Fore.YELLOW}To resume, run:{Style.RESET_ALL}")
            click.echo(f"  ai-governance codebase-refactor --resume {session_id} --target \"{resume_info.get('target', '')}\" ...")

    elif delete_session:
        if state_manager.delete_checkpoint(delete_session):
            click.echo(f"{Fore.GREEN}✓ Session {delete_session} deleted{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.RED}✗ Session {delete_session} not found{Style.RESET_ALL}")

    elif clean_days is not None:
        deleted = state_manager.clean_old_checkpoints(days=clean_days)
        click.echo(f"{Fore.GREEN}✓ Deleted {deleted} session(s) older than {clean_days} days{Style.RESET_ALL}")

    else:
        # Default: list sessions
        state_manager.display_sessions()


@cli.command()
@click.option(
    '--host',
    default='127.0.0.1',
    help='Host to bind the server to (default: 127.0.0.1)'
)
@click.option(
    '--port',
    '-p',
    default=5000,
    help='Port to bind the server to (default: 5000)'
)
@click.option(
    '--no-debug',
    is_flag=True,
    help='Disable debug mode'
)
def dashboard(host, port, no_debug):
    """Launch the web-based audit dashboard.

    The dashboard provides a visual interface to view audit logs,
    track costs and token usage over time, and analyze refactoring patterns.

    Example:
        ai-governance dashboard
        ai-governance dashboard --port 8080
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Dashboard{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    try:
        from .web_ui import run_server

        click.echo(f"{Fore.GREEN}Starting web dashboard...{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}Open your browser to: http://{host}:{port}{Style.RESET_ALL}\n")

        run_server(host=host, port=port, debug=not no_debug)

    except ImportError as e:
        click.echo(f"{Fore.RED}Error: Flask is not installed{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}Install it with: pip install flask{Style.RESET_ALL}")
        click.echo(f"{Fore.DIM}Full error: {e}{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"{Fore.RED}Error starting dashboard: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    cli()
