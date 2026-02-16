"""Analyzes the impact of code changes across the codebase."""

import ast
import difflib
from typing import Dict, List, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
import click
from colorama import Fore, Style


@dataclass
class ImpactReport:
    """Report of change impact analysis."""
    changed_file: str
    directly_affected: List[str]  # Files that import from changed file
    indirectly_affected: List[str]  # Files affected through transitive dependencies
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    change_summary: Dict[str, int]  # Types of changes made
    recommendations: List[str]  # Actions to take


class ImpactAnalyzer:
    """Analyzes the impact of code changes on the codebase."""

    def analyze_change_impact(
        self,
        file_path: str,
        original_code: str,
        new_code: str,
        dep_graph: Dict,
        all_files: List[str]
    ) -> ImpactReport:
        """
        Analyze the impact of changes to a file.

        Args:
            file_path: Path to changed file
            original_code: Original file content
            new_code: New file content
            dep_graph: Dependency graph
            all_files: All files in the codebase

        Returns:
            ImpactReport with detailed analysis
        """
        # Analyze what changed
        change_summary = self._analyze_changes(file_path, original_code, new_code)

        # Find directly affected files (import from this file)
        directly_affected = self._find_direct_dependents(file_path, dep_graph, all_files)

        # Find indirectly affected files (transitive dependencies)
        indirectly_affected = self._find_indirect_dependents(
            file_path,
            directly_affected,
            dep_graph,
            all_files
        )

        # Assess risk level
        risk_level = self._assess_risk(
            change_summary,
            directly_affected,
            indirectly_affected,
            dep_graph
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            file_path,
            change_summary,
            directly_affected,
            indirectly_affected,
            risk_level
        )

        return ImpactReport(
            changed_file=file_path,
            directly_affected=directly_affected,
            indirectly_affected=indirectly_affected,
            risk_level=risk_level,
            change_summary=change_summary,
            recommendations=recommendations
        )

    def _analyze_changes(
        self,
        file_path: str,
        original: str,
        new: str
    ) -> Dict[str, int]:
        """
        Analyze what types of changes were made.

        Returns:
            Dict with change counts by type
        """
        changes = {
            'lines_added': 0,
            'lines_removed': 0,
            'lines_modified': 0,
            'functions_added': 0,
            'functions_removed': 0,
            'functions_modified': 0,
            'classes_added': 0,
            'classes_removed': 0,
            'imports_changed': 0
        }

        # Line-level diff
        diff = list(difflib.unified_diff(
            original.splitlines(),
            new.splitlines(),
            lineterm=''
        ))

        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                changes['lines_added'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                changes['lines_removed'] += 1

        # For Python files, analyze structural changes
        if file_path.endswith('.py'):
            try:
                old_tree = ast.parse(original)
                new_tree = ast.parse(new)

                old_funcs = {node.name for node in ast.walk(old_tree) if isinstance(node, ast.FunctionDef)}
                new_funcs = {node.name for node in ast.walk(new_tree) if isinstance(node, ast.FunctionDef)}

                changes['functions_added'] = len(new_funcs - old_funcs)
                changes['functions_removed'] = len(old_funcs - new_funcs)
                changes['functions_modified'] = len(old_funcs & new_funcs)

                old_classes = {node.name for node in ast.walk(old_tree) if isinstance(node, ast.ClassDef)}
                new_classes = {node.name for node in ast.walk(new_tree) if isinstance(node, ast.ClassDef)}

                changes['classes_added'] = len(new_classes - old_classes)
                changes['classes_removed'] = len(old_classes - new_classes)

                # Check import changes
                old_imports = self._extract_imports(old_tree)
                new_imports = self._extract_imports(new_tree)
                if old_imports != new_imports:
                    changes['imports_changed'] = 1

            except SyntaxError:
                pass  # Can't parse, skip structural analysis

        return changes

    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """Extract import statements from AST."""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return imports

    def _find_direct_dependents(
        self,
        file_path: str,
        dep_graph: Dict,
        all_files: List[str]
    ) -> List[str]:
        """Find files that directly import from the changed file."""
        dependents = []
        file_normalized = file_path.replace('/', '.').replace('\\', '.').replace('.py', '').replace('.js', '').replace('.ts', '')

        for other_file in all_files:
            if other_file == file_path:
                continue

            # Check imports
            imports = dep_graph.get('imports', {}).get(other_file, [])
            for imp in imports:
                module = imp.get('module', '')
                if module in file_path or file_normalized in module or module in file_normalized:
                    dependents.append(other_file)
                    break

        return dependents

    def _find_indirect_dependents(
        self,
        file_path: str,
        direct_dependents: List[str],
        dep_graph: Dict,
        all_files: List[str]
    ) -> List[str]:
        """Find files affected through transitive dependencies."""
        indirect = set()
        visited = set([file_path] + direct_dependents)
        queue = direct_dependents.copy()

        # BFS to find transitive dependencies
        while queue:
            current = queue.pop(0)
            dependents = self._find_direct_dependents(current, dep_graph, all_files)

            for dep in dependents:
                if dep not in visited:
                    indirect.add(dep)
                    visited.add(dep)
                    queue.append(dep)

        return list(indirect)

    def _assess_risk(
        self,
        changes: Dict[str, int],
        direct: List[str],
        indirect: List[str],
        dep_graph: Dict
    ) -> str:
        """
        Assess the risk level of changes.

        Risk factors:
        - Number of affected files
        - Type of changes (breaking vs non-breaking)
        - Removal of functions/classes
        """
        risk_score = 0

        # Factor 1: Affected files
        total_affected = len(direct) + len(indirect)
        if total_affected >= 10:
            risk_score += 40
        elif total_affected >= 5:
            risk_score += 25
        elif total_affected >= 2:
            risk_score += 10

        # Factor 2: Removed functions/classes (breaking changes)
        if changes.get('functions_removed', 0) > 0:
            risk_score += 30
        if changes.get('classes_removed', 0) > 0:
            risk_score += 30

        # Factor 3: Import changes
        if changes.get('imports_changed', 0) > 0:
            risk_score += 15

        # Factor 4: Scale of changes
        total_changes = changes.get('lines_added', 0) + changes.get('lines_removed', 0)
        if total_changes >= 100:
            risk_score += 20
        elif total_changes >= 50:
            risk_score += 10

        # Classify risk
        if risk_score >= 70:
            return 'critical'
        elif risk_score >= 40:
            return 'high'
        elif risk_score >= 20:
            return 'medium'
        else:
            return 'low'

    def _generate_recommendations(
        self,
        file_path: str,
        changes: Dict[str, int],
        direct: List[str],
        indirect: List[str],
        risk_level: str
    ) -> List[str]:
        """Generate actionable recommendations based on impact."""
        recommendations = []

        # Based on affected files
        if len(direct) > 0:
            recommendations.append(
                f"Review {len(direct)} file(s) that directly import from {file_path}"
            )

        if len(indirect) > 5:
            recommendations.append(
                f"High transitive impact: {len(indirect)} files indirectly affected"
            )

        # Based on changes
        if changes.get('functions_removed', 0) > 0:
            recommendations.append(
                f"⚠️  {changes['functions_removed']} function(s) removed - verify no breaking changes"
            )

        if changes.get('classes_removed', 0) > 0:
            recommendations.append(
                f"⚠️  {changes['classes_removed']} class(es) removed - check dependent code"
            )

        if changes.get('imports_changed', 0) > 0:
            recommendations.append(
                "Import structure changed - verify module resolution"
            )

        # Based on risk level
        if risk_level in ['high', 'critical']:
            recommendations.append(
                "🔴 HIGH RISK: Run comprehensive test suite before deploying"
            )
            recommendations.append(
                "Consider creating a backup branch before proceeding"
            )

        if len(direct) + len(indirect) > 0:
            recommendations.append(
                "Run tests for affected files to ensure compatibility"
            )

        if not recommendations:
            recommendations.append("✓ Changes appear to be low risk")

        return recommendations

    def display_impact_report(self, report: ImpactReport):
        """Display impact report in a user-friendly format."""
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{Style.BRIGHT}CHANGE IMPACT ANALYSIS{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}\n")

        # File
        click.echo(f"{Fore.YELLOW}File:{Style.RESET_ALL} {report.changed_file}\n")

        # Risk level
        risk_colors = {
            'low': Fore.GREEN,
            'medium': Fore.YELLOW,
            'high': Fore.RED,
            'critical': Fore.RED + Style.BRIGHT
        }
        risk_color = risk_colors.get(report.risk_level, Fore.WHITE)
        click.echo(f"{Fore.YELLOW}Risk Level:{Style.RESET_ALL} {risk_color}{report.risk_level.upper()}{Style.RESET_ALL}\n")

        # Change summary
        click.echo(f"{Fore.YELLOW}Changes Made:{Style.RESET_ALL}")
        changes = report.change_summary
        if changes.get('lines_added', 0) > 0:
            click.echo(f"  + {changes['lines_added']} lines added")
        if changes.get('lines_removed', 0) > 0:
            click.echo(f"  - {changes['lines_removed']} lines removed")
        if changes.get('functions_added', 0) > 0:
            click.echo(f"  + {changes['functions_added']} function(s) added")
        if changes.get('functions_removed', 0) > 0:
            click.echo(f"  - {changes['functions_removed']} function(s) removed")
        if changes.get('classes_added', 0) > 0:
            click.echo(f"  + {changes['classes_added']} class(es) added")
        if changes.get('classes_removed', 0) > 0:
            click.echo(f"  - {changes['classes_removed']} class(es) removed")
        click.echo()

        # Affected files
        click.echo(f"{Fore.YELLOW}Impact:{Style.RESET_ALL}")
        click.echo(f"  Directly affected: {len(report.directly_affected)} file(s)")
        if report.directly_affected:
            for f in report.directly_affected[:5]:
                click.echo(f"    • {f}")
            if len(report.directly_affected) > 5:
                click.echo(f"    ... and {len(report.directly_affected) - 5} more")

        click.echo(f"  Indirectly affected: {len(report.indirectly_affected)} file(s)")
        if report.indirectly_affected and len(report.indirectly_affected) <= 5:
            for f in report.indirectly_affected:
                click.echo(f"    • {f}")
        click.echo()

        # Recommendations
        if report.recommendations:
            click.echo(f"{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
            for rec in report.recommendations:
                # Highlight warnings
                if '⚠️' in rec or '🔴' in rec:
                    click.echo(f"  {Fore.RED}{rec}{Style.RESET_ALL}")
                elif '✓' in rec:
                    click.echo(f"  {Fore.GREEN}{rec}{Style.RESET_ALL}")
                else:
                    click.echo(f"  • {rec}")
            click.echo()

    def analyze_batch_impact(
        self,
        refactor_results: Dict[str, Dict],
        dep_graph: Dict,
        all_files: List[str]
    ) -> Dict[str, ImpactReport]:
        """
        Analyze impact of multiple file changes.

        Args:
            refactor_results: Dict of {file_path: result}
            dep_graph: Dependency graph
            all_files: All files in codebase

        Returns:
            Dict of {file_path: ImpactReport}
        """
        impact_reports = {}

        for file_path, result in refactor_results.items():
            if result.get('success'):
                original = result.get('original_code', '')
                new = result.get('refactored_code', '')

                if original and new:
                    report = self.analyze_change_impact(
                        file_path,
                        original,
                        new,
                        dep_graph,
                        all_files
                    )
                    impact_reports[file_path] = report

        return impact_reports
