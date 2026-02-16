"""
Codebase-wide refactoring orchestrator with dependency awareness.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import click
from colorama import Fore, Style

from .dependency_analyzer import DependencyAnalyzer
from .ai_client import AIClient
from .scanner import Scanner
from .validators import CrossFileValidator, ValidationResult, TypeChecker
from .diff_manager import DiffManager
from .audit_logger import AuditLogger
from .call_graph_analyzer import CallGraphAnalyzer
from .context_selector import ContextSelector
from .refactor_planner import RefactorPlanner
from .test_runner import TestRunner
from .refactor_state import RefactorState
from .impact_analyzer import ImpactAnalyzer


class RefactorError(Exception):
    """Exception raised when refactoring fails."""
    pass


class CodebaseRefactor:
    """Orchestrates whole-codebase refactoring with dependency awareness."""

    def __init__(
        self,
        api_key: str,
        policy_path: str = "ai_governance/profiles/default-secure.yaml",
        enable_validation: bool = True,
        enable_type_checking: bool = False,
        enable_testing: bool = False,
        enable_impact_analysis: bool = True,
        enable_resume: bool = True,
        show_plan: bool = True
    ):
        """
        Initialize codebase refactor orchestrator.

        Args:
            api_key: Anthropic API key
            policy_path: Path to security policy file
            enable_validation: Enable cross-file validation
            enable_type_checking: Enable external type checkers (mypy, tsc)
            enable_testing: Enable running tests to validate changes
            enable_impact_analysis: Enable change impact analysis
            enable_resume: Enable checkpoint/resume functionality
            show_plan: Display refactoring plan before execution
        """
        self.ai_client = AIClient(api_key)
        self.scanner = Scanner(policy_path)
        self.dependency_analyzer = DependencyAnalyzer()
        self.call_graph_analyzer = CallGraphAnalyzer()
        self.context_selector = ContextSelector()
        self.refactor_planner = RefactorPlanner()
        self.test_runner = TestRunner() if enable_testing else None
        self.refactor_state = RefactorState() if enable_resume else None
        self.impact_analyzer = ImpactAnalyzer() if enable_impact_analysis else None
        self.enable_validation = enable_validation
        self.enable_type_checking = enable_type_checking
        self.enable_testing = enable_testing
        self.enable_impact_analysis = enable_impact_analysis
        self.enable_resume = enable_resume
        self.show_plan = show_plan
        self.audit_logger = AuditLogger()

    def refactor_codebase(
        self,
        file_paths: List[str],
        target: str,
        dry_run: bool = False,
        create_backup: bool = True,
        resume_session: Optional[str] = None
    ) -> Dict:
        """
        Refactor entire codebase with dependency awareness.

        Args:
            file_paths: List of file paths to refactor
            target: Refactoring goal description
            dry_run: If True, only show what would change without applying
            create_backup: Create backups before applying changes
            resume_session: Optional session ID to resume from

        Returns:
            Dict with refactoring results and statistics

        Raises:
            RefactorError: If refactoring fails validation
        """
        click.echo(f"\n{'='*70}")
        click.echo("CODEBASE-WIDE REFACTORING (ENHANCED)")
        click.echo(f"{'='*70}")
        click.echo(f"Files to refactor: {len(file_paths)}")
        click.echo(f"Refactoring goal: {target}")
        click.echo(f"Validation: {'enabled' if self.enable_validation else 'disabled'}")
        click.echo(f"Type checking: {'enabled' if self.enable_type_checking else 'disabled'}")
        click.echo(f"Testing: {'enabled' if self.enable_testing else 'disabled'}")
        click.echo(f"Impact analysis: {'enabled' if self.enable_impact_analysis else 'disabled'}")
        click.echo()

        # Check for resume
        if resume_session and self.enable_resume:
            return self._resume_refactoring(resume_session, target, dry_run, create_backup)

        # Generate session ID for checkpointing
        session_id = None
        if self.enable_resume:
            session_id = self.refactor_state.generate_session_id(file_paths, target)
            click.echo(f"Session ID: {session_id}\n")

        # Phase 1: Analyze dependencies and build call graph
        click.echo("[1/8] Analyzing dependencies and call graph...")
        dep_graph = self._analyze_dependencies(file_paths)
        click.echo(f"  ✓ Found {len(dep_graph['groups'])} file clusters")
        click.echo(f"  ✓ Determined refactoring order for {len(dep_graph['order'])} files")

        if 'call_graph' in dep_graph:
            hot_spots = dep_graph['call_graph'].get('hot_spots', [])
            if hot_spots:
                click.echo(f"  ✓ Identified {len(hot_spots)} hot-spot functions")
        click.echo()

        # Phase 2: Create and display refactoring plan
        if self.show_plan:
            click.echo("[2/8] Creating refactoring plan...")
            plan = self.refactor_planner.create_plan(file_paths, target, dep_graph)
            self.refactor_planner.display_plan(plan, show_details=True)

            if not dry_run:
                if not click.confirm("\nProceed with this plan?", default=True):
                    click.echo("Refactoring cancelled by user")
                    return {'cancelled': True}
        click.echo()

        # Phase 3: Security scanning
        click.echo("[3/8] Running security scans...")
        scan_results = self._scan_files(file_paths)

        blocked_files = scan_results['blocked']
        allowed_files = scan_results['allowed']

        if blocked_files:
            click.echo(f"  ⚠  {len(blocked_files)} file(s) blocked by security policy (will be skipped):")
            for blocked_file in blocked_files[:10]:  # Show first 10
                click.echo(f"    - {blocked_file}")
            if len(blocked_files) > 10:
                click.echo(f"    ... and {len(blocked_files) - 10} more")
            click.echo()

        if not allowed_files:
            click.echo(f"  ✗ All files blocked by security policy. Nothing to refactor.")
            raise RefactorError("All files blocked by security policy")

        click.echo(f"  ✓ {len(allowed_files)} file(s) passed security checks and will be refactored")
        if blocked_files:
            click.echo(f"  ℹ  {len(blocked_files)} file(s) will be skipped")
        click.echo()

        # Update file list to only include allowed files
        file_paths_to_refactor = allowed_files

        # Update dependency graph to only include allowed files
        dep_graph = self._filter_dep_graph_for_allowed_files(dep_graph, allowed_files)

        # Save initial checkpoint with allowed files only
        if self.enable_resume and not dry_run:
            self.refactor_state.save_checkpoint(
                session_id=session_id,
                completed_files=[],
                failed_files={blocked_file: "Blocked by security policy" for blocked_file in blocked_files},
                pending_files=file_paths_to_refactor,
                target=target,
                dep_graph=dep_graph,
                refactor_results={}
            )

        # Phase 4: Refactor in groups with smart context
        click.echo("[4/8] Refactoring files (with smart context selection)...")
        refactor_results = self._refactor_in_groups(
            dep_graph,
            target,
            file_paths_to_refactor,
            session_id
        )

        # Add blocked files to results for reporting
        for blocked_file in blocked_files:
            refactor_results[blocked_file] = {
                'success': False,
                'error': 'Blocked by security policy',
                'blocked': True,
                'original_code': '',
                'refactored_code': '',
                'tokens_used': {'input': 0, 'output': 0, 'total': 0},
                'cost': 0.0
            }

        successful = sum(1 for r in refactor_results.values() if r['success'])
        click.echo(f"  ✓ Successfully refactored {successful}/{len(file_paths)} files")

        if successful < len(file_paths):
            failed = len(file_paths) - successful
            click.echo(f"  ✗ {failed} files failed refactoring")
            for path, result in refactor_results.items():
                if not result['success']:
                    click.echo(f"    - {path}: {result.get('error', 'Unknown error')}")
        click.echo()

        # Phase 5: Impact analysis
        if self.enable_impact_analysis and successful > 0:
            click.echo("[5/8] Analyzing change impact...")
            self._analyze_impact(refactor_results, dep_graph, file_paths)
        else:
            click.echo("[5/8] Impact analysis skipped")
        click.echo()

        # Phase 6: Validate cross-file consistency
        if self.enable_validation:
            click.echo("[6/8] Validating cross-file consistency...")
            validation_result = self._validate_refactoring(
                refactor_results,
                dep_graph
            )

            if not validation_result.passed:
                click.echo(f"  ✗ Validation failed with {len(validation_result.errors)} errors")
                for error in validation_result.errors[:5]:  # Show first 5
                    click.echo(f"    - {error}")

                if not dry_run:
                    click.echo("\n  Rolling back changes...")
                    raise RefactorError("Cross-file validation failed")
            else:
                click.echo(f"  ✓ All cross-file validations passed")
                if validation_result.warnings:
                    click.echo(f"  ⚠ {len(validation_result.warnings)} warnings")
        else:
            click.echo("[6/8] Validation skipped")
        click.echo()

        # Phase 7: Run tests
        if self.enable_testing and self.test_runner:
            click.echo("[7/8] Running tests...")
            test_result = self.test_runner.run_tests()

            if not test_result.passed:
                click.echo(f"  ✗ {len(test_result.errors)} test(s) failed")
                for error in test_result.errors[:5]:
                    click.echo(f"    - {error}")

                if not dry_run:
                    if not click.confirm("\n  Tests failed. Continue anyway?", default=False):
                        raise RefactorError("Tests failed after refactoring")
            else:
                click.echo(f"  ✓ Tests passed")
                for warning in test_result.warnings:
                    click.echo(f"    {warning}")
        else:
            click.echo("[7/8] Testing skipped")
        click.echo()

        # Phase 8: Type checking (optional)
        if self.enable_type_checking:
            click.echo("[8/8] Running type checkers...")
            type_check_result = self._run_type_checking(refactor_results)

            if not type_check_result.passed:
                click.echo(f"  ✗ Type checking failed")
                for error in type_check_result.errors[:5]:
                    click.echo(f"    - {error}")
            else:
                click.echo(f"  ✓ Type checking passed")
        else:
            click.echo("[8/8] Type checking skipped")
        click.echo()

        # Apply changes
        if not dry_run:
            click.echo("Applying changes...")

            if create_backup:
                backup_dir = self._create_backups(refactor_results)
                click.echo(f"  ✓ Created backups in {backup_dir}")

            applied = self._apply_changes(refactor_results)
            click.echo(f"  ✓ Applied changes to {applied} files")

            # Log to audit
            self._log_refactoring(refactor_results, target, dep_graph)
        else:
            click.echo("Dry run - no changes applied")

        click.echo()

        # Summary
        return self._generate_summary(refactor_results, dep_graph, dry_run)

    def _analyze_dependencies(self, file_paths: List[str]) -> Dict:
        """Analyze file dependencies and build comprehensive graph including call graph."""
        # Get basic dependency graph
        dep_graph = self.dependency_analyzer.analyze_project(file_paths)

        # Add call graph analysis
        file_contents = {}
        for fp in file_paths:
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    file_contents[fp] = f.read()
            except Exception:
                pass

        if file_contents:
            call_graph = self.call_graph_analyzer.build_call_graph(file_contents)
            dep_graph['call_graph'] = call_graph

        return dep_graph

    def _filter_dep_graph_for_allowed_files(self, dep_graph: Dict, allowed_files: List[str]) -> Dict:
        """
        Filter dependency graph to only include allowed files.

        This ensures that blocked files are excluded from:
        - File ordering
        - Grouping
        - Context selection

        Args:
            dep_graph: Original dependency graph
            allowed_files: List of files that passed security checks

        Returns:
            Filtered dependency graph
        """
        allowed_set = set(allowed_files)
        filtered = {}

        # Filter imports
        if 'imports' in dep_graph:
            filtered['imports'] = {
                f: imports for f, imports in dep_graph['imports'].items()
                if f in allowed_set
            }

        # Filter exports
        if 'exports' in dep_graph:
            filtered['exports'] = {
                f: exports for f, exports in dep_graph['exports'].items()
                if f in allowed_set
            }

        # Filter callers
        if 'callers' in dep_graph:
            filtered['callers'] = dep_graph['callers']  # Keep for reference

        # Filter groups (only include groups with allowed files)
        if 'groups' in dep_graph:
            filtered['groups'] = [
                [f for f in group if f in allowed_set]
                for group in dep_graph['groups']
            ]
            # Remove empty groups
            filtered['groups'] = [g for g in filtered['groups'] if g]

        # Filter order (only allowed files)
        if 'order' in dep_graph:
            filtered['order'] = [f for f in dep_graph['order'] if f in allowed_set]

        # Keep call graph for reference (it has global info)
        if 'call_graph' in dep_graph:
            filtered['call_graph'] = dep_graph['call_graph']

        return filtered

    def _scan_files(self, file_paths: List[str]) -> Dict:
        """Scan files for security issues."""
        results = {
            'allowed': [],
            'blocked': []
        }

        for file_path in file_paths:
            scan_result = self.scanner.scan_file(file_path)

            if scan_result['allowed']:
                results['allowed'].append(file_path)
            else:
                results['blocked'].append(file_path)

        return results

    def _refactor_in_groups(
        self,
        dep_graph: Dict,
        target: str,
        all_files: List[str],
        session_id: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Refactor files in groups based on dependencies with smart context selection.

        Args:
            dep_graph: Dependency graph with groups and order
            target: Refactoring goal
            all_files: All files to refactor
            session_id: Optional session ID for checkpointing

        Returns:
            Dict of {file_path: refactor_result}
        """
        results = {}
        groups = dep_graph['groups']
        order = dep_graph['order']

        # Read all file contents first
        file_contents = {}
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                results[file_path] = {
                    'success': False,
                    'error': f"Failed to read file: {e}",
                    'original_code': '',
                    'refactored_code': ''
                }

        # Process each group
        for i, group in enumerate(groups, 1):
            # Only process files in this group that are in all_files
            group_files = [f for f in group if f in all_files]

            if not group_files:
                continue

            click.echo(f"  Processing group {i}/{len(groups)} ({len(group_files)} files)...")

            # Refactor each file in the group with context
            for file_path in group_files:
                if file_path in results:
                    continue  # Already failed

                # Gather context using smart context selector
                context_files = self._gather_context(
                    file_path,
                    dep_graph,
                    file_contents
                )

                # Show context selection
                if context_files:
                    summary = self.context_selector.get_context_summary(context_files)
                    click.echo(f"    {file_path}: {summary}")

                # Refactor with context
                code = file_contents[file_path]
                result = self.ai_client.refactor_with_context(
                    code=code,
                    target_description=target,
                    filepath=file_path,
                    context_files=context_files,
                    dependency_info=dep_graph
                )

                # Store original code for impact analysis
                result['original_code'] = code

                results[file_path] = result

                # Update file contents for next iterations
                if result['success']:
                    file_contents[file_path] = result['refactored_code']

                    # Update checkpoint
                    if session_id and self.enable_resume:
                        self.refactor_state.mark_file_completed(session_id, file_path, result)
                else:
                    # Mark as failed in checkpoint
                    if session_id and self.enable_resume:
                        self.refactor_state.mark_file_failed(
                            session_id,
                            file_path,
                            result.get('error', 'Unknown error')
                        )

        return results

    def _gather_context(
        self,
        file_path: str,
        dep_graph: Dict,
        file_contents: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Gather related file context using smart context selection.

        Args:
            file_path: Target file being refactored
            dep_graph: Dependency graph
            file_contents: All file contents

        Returns:
            Dict of {related_file_path: content}
        """
        return self.context_selector.select_context_files(
            target_file=file_path,
            all_files=file_contents,
            dep_graph=dep_graph,
            max_context_files=5,  # Increased from 3
            max_context_tokens=6000  # Token budget for context
        )

    def _validate_refactoring(
        self,
        refactor_results: Dict[str, Dict],
        dep_graph: Dict
    ) -> ValidationResult:
        """Validate refactored code maintains compatibility."""
        # Build original and new file maps
        original_files = {}
        new_files = {}

        for file_path, result in refactor_results.items():
            if result['success']:
                # Read original
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original_files[file_path] = f.read()
                except Exception:
                    pass

                new_files[file_path] = result['refactored_code']

        # Run validation
        validator = CrossFileValidator(original_files)
        return validator.validate_refactoring(new_files, dep_graph)

    def _run_type_checking(
        self,
        refactor_results: Dict[str, Dict]
    ) -> ValidationResult:
        """Run external type checkers."""
        # Collect successful refactorings
        new_files = {
            path: result['refactored_code']
            for path, result in refactor_results.items()
            if result['success']
        }

        # Check Python files
        python_files = {k: v for k, v in new_files.items() if k.endswith('.py')}
        if python_files:
            return TypeChecker.run_python_type_check(python_files)

        # Check TypeScript files
        ts_files = {k: v for k, v in new_files.items() if k.endswith(('.ts', '.tsx'))}
        if ts_files:
            return TypeChecker.run_javascript_type_check(ts_files)

        return ValidationResult(passed=True)

    def _create_backups(self, refactor_results: Dict[str, Dict]) -> str:
        """Create backups of files before applying changes."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f".ai_governance_backups/{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)

        for file_path, result in refactor_results.items():
            if result['success'] and os.path.exists(file_path):
                # Create subdirectories if needed
                backup_path = os.path.join(backup_dir, file_path)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)

                # Copy file
                shutil.copy2(file_path, backup_path)

        return backup_dir

    def _apply_changes(self, refactor_results: Dict[str, Dict]) -> int:
        """Apply refactored code to files."""
        applied = 0

        for file_path, result in refactor_results.items():
            if result['success']:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(result['refactored_code'])
                    applied += 1
                except Exception as e:
                    click.echo(f"  ✗ Failed to write {file_path}: {e}")

        return applied

    def _log_refactoring(
        self,
        refactor_results: Dict[str, Dict],
        target: str,
        dep_graph: Dict
    ):
        """Log refactoring to audit trail."""
        for file_path, result in refactor_results.items():
            if result['success']:
                # Read original content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        original = f.read()
                except Exception:
                    original = ""

                # Log successful refactoring
                self.audit_logger.log_action(
                    action='codebase_refactor',
                    filepath=file_path,
                    status='success',
                    original_code=original,
                    refactored_code=result['refactored_code'],
                    target=target,
                    tokens_used=result['tokens_used']['total'],
                    cost=result['cost'],
                    findings=[]
                )
            elif result.get('blocked', False):
                # Log blocked file
                self.audit_logger.log_action(
                    action='codebase_refactor',
                    filepath=file_path,
                    status='blocked',
                    reason='Blocked by security policy',
                    target=target,
                    tokens_used=0,
                    cost=0.0,
                    findings=[]
                )

    def _analyze_impact(
        self,
        refactor_results: Dict[str, Dict],
        dep_graph: Dict,
        all_files: List[str]
    ):
        """Analyze the impact of changes."""
        if not self.impact_analyzer:
            return

        high_risk_count = 0

        for file_path, result in refactor_results.items():
            if result.get('success'):
                original = result.get('original_code', '')
                new = result.get('refactored_code', '')

                if original and new:
                    report = self.impact_analyzer.analyze_change_impact(
                        file_path,
                        original,
                        new,
                        dep_graph,
                        all_files
                    )

                    # Only display detailed reports for high/critical risk
                    if report.risk_level in ['high', 'critical']:
                        self.impact_analyzer.display_impact_report(report)
                        high_risk_count += 1
                    elif report.risk_level == 'medium':
                        click.echo(f"  ⚠  {file_path}: Medium risk - {len(report.directly_affected)} files directly affected")

        if high_risk_count == 0:
            click.echo(f"  ✓ All changes are low to medium risk")

    def _resume_refactoring(
        self,
        session_id: str,
        target: str,
        dry_run: bool,
        create_backup: bool
    ) -> Dict:
        """Resume a previous refactoring session."""
        click.echo(f"\nResuming session: {session_id}\n")

        # Load checkpoint
        resume_info = self.refactor_state.get_resume_info(session_id)
        if not resume_info:
            raise RefactorError(f"Session {session_id} not found or cannot be resumed")

        pending_files = resume_info['pending_files']
        completed_files = resume_info['completed_files']
        failed_files = resume_info['failed_files']

        click.echo(f"Progress so far:")
        click.echo(f"  Completed: {len(completed_files)} files")
        click.echo(f"  Failed: {len(failed_files)} files")
        click.echo(f"  Remaining: {len(pending_files)} files\n")

        if not pending_files:
            click.echo("No pending files to process. Session is complete.")
            return {'resumed': True, 'completed': len(completed_files)}

        # Continue with pending files
        dep_graph = resume_info.get('dependency_graph', {})

        click.echo(f"Continuing with {len(pending_files)} remaining files...\n")

        # Run the refactoring on pending files
        return self.refactor_codebase(
            file_paths=pending_files,
            target=target,
            dry_run=dry_run,
            create_backup=create_backup,
            resume_session=None  # Don't recurse
        )

    def _generate_summary(
        self,
        refactor_results: Dict[str, Dict],
        dep_graph: Dict,
        dry_run: bool
    ) -> Dict:
        """Generate summary statistics."""
        successful = [r for r in refactor_results.values() if r['success']]
        blocked = [r for r in refactor_results.values() if not r['success'] and r.get('blocked', False)]
        failed = [r for r in refactor_results.values() if not r['success'] and not r.get('blocked', False)]

        total_cost = sum(r.get('cost', 0) for r in successful)
        total_tokens = sum(r.get('tokens_used', {}).get('total', 0) for r in successful)

        summary = {
            'total_files': len(refactor_results),
            'successful': len(successful),
            'blocked': len(blocked),
            'failed': len(failed),
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'groups': len(dep_graph.get('groups', [])),
            'dry_run': dry_run
        }

        # Display summary
        click.echo(f"{'='*70}")
        click.echo("REFACTORING SUMMARY")
        click.echo(f"{'='*70}")
        click.echo(f"Total files:     {summary['total_files']}")
        click.echo(f"Successful:      {summary['successful']}")

        if blocked:
            click.echo(f"Blocked:         {summary['blocked']} (security policy)")

        if failed:
            click.echo(f"Failed:          {summary['failed']}")

        click.echo(f"File groups:     {summary['groups']}")
        click.echo(f"Total cost:      ${summary['total_cost']:.4f}")
        click.echo(f"Total tokens:    {summary['total_tokens']:,}")

        if dry_run:
            click.echo(f"\nDRY RUN - No changes were applied")

        # Show details about blocked files
        if blocked:
            click.echo(f"\n{Fore.YELLOW}Blocked Files (skipped):{Style.RESET_ALL}")
            blocked_files = [path for path, r in refactor_results.items() if r.get('blocked', False)]
            for bf in blocked_files[:10]:
                click.echo(f"  • {bf}")
            if len(blocked_files) > 10:
                click.echo(f"  ... and {len(blocked_files) - 10} more")

        click.echo(f"{'='*70}\n")

        return summary
