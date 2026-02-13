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

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()


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
            target_description=target
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
def init():
    """Initialize AI Governance configuration.

    Creates a .env template and shows setup instructions.
    """
    click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}AI Governance Tool - Initialization{Style.RESET_ALL}")
    click.echo(f"{'=' * 70}\n")

    # Create .env template
    env_template = """# AI Governance Tool Configuration
# Copy this to .env and add your API key

ANTHROPIC_API_KEY=your_api_key_here
"""

    env_path = Path.cwd() / ".env.template"
    with open(env_path, 'w') as f:
        f.write(env_template)

    click.echo(f"{Fore.GREEN}✅ Created .env.template{Style.RESET_ALL}\n")
    click.echo(f"{Fore.YELLOW}Setup Instructions:{Style.RESET_ALL}")
    click.echo("1. Copy .env.template to .env")
    click.echo("2. Add your Anthropic API key to .env")
    click.echo("3. Run: ai-governance refactor <file> --target <description>\n")

    click.echo(f"{Fore.CYAN}Policy Configuration:{Style.RESET_ALL}")
    click.echo(f"Default policy: profiles/default-secure.yaml")
    click.echo(f"Customize by editing the YAML file or creating your own\n")

    click.echo(f"{Fore.CYAN}Audit Logging:{Style.RESET_ALL}")
    click.echo(f"Audit log: .ai-governance-audit.db")
    click.echo(f"View logs with: ai-governance audit\n")


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


if __name__ == '__main__':
    cli()
