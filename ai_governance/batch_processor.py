"""
Batch Processing Module for AI Governance Tool.

Handles bulk refactoring operations across multiple files.
"""

from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from colorama import Fore, Style


@dataclass
class BatchResult:
    """Result of a batch refactoring operation."""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0

    # Detailed results per file
    file_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Aggregated statistics
    total_cost: float = 0.0
    total_tokens: int = 0

    def add_result(self, filepath: str, status: str, **kwargs):
        """Add a result for a single file."""
        self.file_results[filepath] = {
            'status': status,
            **kwargs
        }

        # Update counters
        if status == 'success':
            self.successful += 1
            self.total_cost += kwargs.get('cost', 0.0)
            self.total_tokens += kwargs.get('tokens_used', 0)
        elif status == 'blocked':
            self.blocked += 1
        elif status == 'failed':
            self.failed += 1
        elif status == 'skipped':
            self.skipped += 1

    def get_summary(self) -> str:
        """Get a summary of the batch operation."""
        lines = [
            f"\n{Fore.CYAN}{Style.BRIGHT}Batch Refactoring Summary{Style.RESET_ALL}",
            f"{'=' * 70}",
            f"Total files:     {self.total_files}",
            f"{Fore.GREEN}Successful:      {self.successful}{Style.RESET_ALL}",
            f"{Fore.RED}Failed:          {self.failed}{Style.RESET_ALL}",
            f"{Fore.YELLOW}Blocked:         {self.blocked}{Style.RESET_ALL}",
            f"{Fore.BLUE}Skipped:         {self.skipped}{Style.RESET_ALL}",
            f"",
            f"Total cost:      ${self.total_cost:.6f}",
            f"Total tokens:    {self.total_tokens}",
            f"{'=' * 70}\n"
        ]
        return '\n'.join(lines)


class BatchProcessor:
    """Processes multiple files for refactoring."""

    def __init__(self, policy_engine, scanner, ai_client, diff_manager,
                 audit_logger, no_backup=False, dry_run=False, apply=False):
        """
        Initialize BatchProcessor.

        Args:
            policy_engine: PolicyEngine instance
            scanner: Scanner instance
            ai_client: AIClient instance
            diff_manager: DiffManager instance
            audit_logger: AuditLogger instance
            no_backup: Whether to skip backups
            dry_run: Whether to run in dry-run mode
            apply: Whether to auto-apply changes without confirmation
        """
        self.policy_engine = policy_engine
        self.scanner = scanner
        self.ai_client = ai_client
        self.diff_manager = diff_manager
        self.audit_logger = audit_logger
        self.no_backup = no_backup
        self.dry_run = dry_run
        self.apply = apply

    def process_files(self, files: List[Path], target: str,
                      show_progress: bool = True) -> BatchResult:
        """
        Process multiple files for refactoring.

        Args:
            files: List of file paths to process
            target: Refactoring target description
            show_progress: Whether to show progress updates

        Returns:
            BatchResult with statistics and results
        """
        import click

        result = BatchResult()
        result.total_files = len(files)

        for idx, filepath in enumerate(files, 1):
            if show_progress:
                click.echo(f"\n{Fore.CYAN}[{idx}/{result.total_files}] Processing: {filepath}{Style.RESET_ALL}")
                click.echo(f"{'-' * 70}")

            file_result = self._process_single_file(
                filepath=str(filepath),
                target=target
            )

            result.add_result(
                filepath=str(filepath),
                **file_result
            )

        return result

    def _process_single_file(self, filepath: str, target: str) -> Dict[str, Any]:
        """
        Process a single file for refactoring.

        Args:
            filepath: Path to the file
            target: Refactoring target description

        Returns:
            Dictionary with processing result
        """
        import click

        # Scan file
        scan_result = self.scanner.scan_file(filepath)

        # Handle errors
        if scan_result.get('error'):
            click.echo(f"{Fore.RED}❌ ERROR: {scan_result['reason']}{Style.RESET_ALL}")
            self.audit_logger.log_action(
                filepath=filepath,
                action='refactor',
                status='error',
                reason=scan_result['reason']
            )
            return {
                'status': 'failed',
                'reason': scan_result['reason']
            }

        # Handle blocked files
        if not scan_result['allowed']:
            click.echo(f"{Fore.YELLOW}🚫 BLOCKED: {scan_result['reason']}{Style.RESET_ALL}")

            # Log blocked attempt
            self.audit_logger.log_action(
                filepath=filepath,
                action='refactor',
                status='blocked',
                reason=scan_result['reason'],
                findings=scan_result['findings'],
                target_description=target
            )

            return {
                'status': 'blocked',
                'reason': scan_result['reason'],
                'findings': scan_result.get('findings', [])
            }

        # File passed security checks
        click.echo(f"{Fore.GREEN}✅ PASSED security scan{Style.RESET_ALL}")

        if self.dry_run:
            click.echo(f"{Fore.YELLOW}Dry run - skipping refactoring{Style.RESET_ALL}")
            self.audit_logger.log_action(
                filepath=filepath,
                action='scan',
                status='allowed',
                reason=scan_result['reason']
            )
            return {
                'status': 'skipped',
                'reason': 'dry run mode'
            }

        # Refactor with AI
        try:
            result = self.ai_client.refactor_code(
                code=scan_result['content'],
                target_description=target,
                filepath=filepath
            )

            if not result['success']:
                click.echo(f"{Fore.RED}❌ Refactoring failed: {result['error']}{Style.RESET_ALL}")
                self.audit_logger.log_action(
                    filepath=filepath,
                    action='refactor',
                    status='error',
                    reason=result['error'],
                    target_description=target,
                    model=result['model']
                )
                return {
                    'status': 'failed',
                    'reason': result['error']
                }

            # Success!
            click.echo(f"{Fore.GREEN}✅ Refactored - Cost: ${result['cost']:.6f}, "
                      f"Tokens: {result['tokens_used']['total']}{Style.RESET_ALL}")

            # Log success
            self.audit_logger.log_action(
                filepath=filepath,
                action='refactor',
                status='success',
                reason='Refactoring completed successfully',
                tokens_used=result['tokens_used']['total'],
                cost=result['cost'],
                model=result['model'],
                target_description=target
            )

            # Apply changes if in batch mode (we auto-apply in batch)
            if self.apply:
                # Create backup
                if not self.no_backup:
                    backup_path = self.diff_manager.create_backup(filepath)
                    if backup_path:
                        click.echo(f"{Fore.BLUE}Backup: {backup_path}{Style.RESET_ALL}")

                # Save refactored code
                if self.diff_manager.save_refactored(filepath, result['refactored_code']):
                    click.echo(f"{Fore.GREEN}Applied changes to {filepath}{Style.RESET_ALL}")
                else:
                    click.echo(f"{Fore.RED}Failed to save changes{Style.RESET_ALL}")
                    return {
                        'status': 'failed',
                        'reason': 'Failed to save changes'
                    }

            return {
                'status': 'success',
                'cost': result['cost'],
                'tokens_used': result['tokens_used']['total'],
                'model': result['model']
            }

        except Exception as e:
            click.echo(f"{Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
            return {
                'status': 'failed',
                'reason': str(e)
            }
