"""Generates and manages refactoring plans."""

from typing import Dict, List, Set
from dataclasses import dataclass
import click
from colorama import Fore, Style


@dataclass
class RefactorStep:
    """A single step in the refactoring plan."""
    step_number: int
    file_path: str
    description: str
    dependencies: List[str]  # Files that must be refactored first
    dependents: List[str]    # Files that depend on this one
    risk_level: str          # 'low', 'medium', 'high'
    estimated_impact: int    # Number of dependent files
    reason: str              # Why this file is at this position


class RefactorPlanner:
    """Plans multi-file refactoring operations."""

    def create_plan(
        self,
        file_paths: List[str],
        target: str,
        dep_graph: Dict
    ) -> List[RefactorStep]:
        """
        Create a step-by-step refactoring plan.

        The plan orders files based on:
        1. Dependency order (topological sort)
        2. Risk assessment (files with fewer dependents first)
        3. Impact analysis (how many files will be affected)

        Args:
            file_paths: List of files to refactor
            target: Refactoring goal description
            dep_graph: Dependency graph with imports, exports, call graph

        Returns:
            List of RefactorStep objects in execution order
        """
        plan = []
        order = dep_graph.get('order', file_paths)
        imports = dep_graph.get('imports', {})
        exports = dep_graph.get('exports', {})
        call_graph = dep_graph.get('call_graph', {})
        callers = call_graph.get('callers', {}) if call_graph else {}

        for i, file_path in enumerate(order, 1):
            # Get dependencies (files this one imports from)
            dependencies = self._get_dependencies(file_path, dep_graph, order[:i-1])

            # Get dependents (files that import from this one)
            dependents = self._get_dependents(file_path, dep_graph, file_paths)

            # Assess risk based on number of dependents
            risk = self._assess_risk(file_path, dependents, exports)

            # Estimate impact
            impact = len(dependents)

            # Generate reason for ordering
            reason = self._generate_reason(file_path, dependencies, dependents, i, len(order))

            step = RefactorStep(
                step_number=i,
                file_path=file_path,
                description=target,
                dependencies=dependencies,
                dependents=dependents,
                risk_level=risk,
                estimated_impact=impact,
                reason=reason
            )
            plan.append(step)

        return plan

    def display_plan(self, plan: List[RefactorStep], show_details: bool = True):
        """
        Display the refactoring plan to user.

        Args:
            plan: List of RefactorStep objects
            show_details: If True, show full details. If False, show summary only.
        """
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{Style.BRIGHT}REFACTORING PLAN{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}\n")

        # Summary statistics
        total_files = len(plan)
        risk_counts = {'low': 0, 'medium': 0, 'high': 0}
        for step in plan:
            risk_counts[step.risk_level] += 1

        click.echo(f"{Fore.YELLOW}Summary:{Style.RESET_ALL}")
        click.echo(f"  Total files:  {total_files}")
        click.echo(f"  Low risk:     {risk_counts['low']} files")
        click.echo(f"  Medium risk:  {risk_counts['medium']} files")
        click.echo(f"  High risk:    {risk_counts['high']} files")
        click.echo()

        if show_details:
            click.echo(f"{Fore.YELLOW}Execution Order:{Style.RESET_ALL}\n")

            for step in plan:
                self._display_step(step)

    def _display_step(self, step: RefactorStep):
        """Display a single refactoring step."""
        # Color code by risk
        risk_color = {
            'low': Fore.GREEN,
            'medium': Fore.YELLOW,
            'high': Fore.RED
        }[step.risk_level]

        # Step header
        click.echo(f"{Fore.CYAN}{step.step_number}. {step.file_path}{Style.RESET_ALL}")

        # Risk level
        click.echo(f"   Risk: {risk_color}{step.risk_level.upper()}{Style.RESET_ALL}")

        # Impact
        impact_str = f"{step.estimated_impact} file(s) will be affected"
        if step.estimated_impact == 0:
            impact_str = "No dependent files"
            impact_color = Fore.GREEN
        elif step.estimated_impact <= 2:
            impact_color = Fore.YELLOW
        else:
            impact_color = Fore.RED

        click.echo(f"   Impact: {impact_color}{impact_str}{Style.RESET_ALL}")

        # Dependencies
        if step.dependencies:
            deps_str = ", ".join(step.dependencies[-3:])  # Show last 3
            if len(step.dependencies) > 3:
                deps_str += f" (and {len(step.dependencies) - 3} more)"
            click.echo(f"   Depends on: {deps_str}")

        # Dependents
        if step.dependents:
            deps_str = ", ".join(step.dependents[:3])  # Show first 3
            if len(step.dependents) > 3:
                deps_str += f" (and {len(step.dependents) - 3} more)"
            click.echo(f"   Used by: {deps_str}")

        # Reason
        if step.reason:
            click.echo(f"   {Fore.DIM}→ {step.reason}{Style.RESET_ALL}")

        click.echo()

    def _assess_risk(
        self,
        file_path: str,
        dependents: List[str],
        exports: Dict
    ) -> str:
        """
        Assess risk level of refactoring this file.

        Risk factors:
        - Number of dependent files
        - Number of exported symbols
        - Whether exports are public APIs
        """
        dependent_count = len(dependents)
        file_exports = exports.get(file_path, [])
        export_count = len(file_exports)

        # High risk: Many dependents OR many exports
        if dependent_count >= 4 or export_count >= 10:
            return 'high'

        # Medium risk: Some dependents OR some exports
        elif dependent_count >= 2 or export_count >= 5:
            return 'medium'

        # Low risk: Few or no dependents and few exports
        else:
            return 'low'

    def _get_dependencies(
        self,
        file_path: str,
        dep_graph: Dict,
        processed: List[str]
    ) -> List[str]:
        """
        Get list of files this file depends on that are being refactored.

        Args:
            file_path: Target file
            dep_graph: Dependency graph
            processed: Files that have been processed before this one

        Returns:
            List of file paths this file depends on
        """
        imports = dep_graph.get('imports', {}).get(file_path, [])
        dependencies = []

        for imp in imports:
            module = imp.get('module', '')

            # Find matching processed file
            for proc_file in processed:
                # Normalize for comparison
                proc_normalized = proc_file.replace('/', '.').replace('\\', '.').replace('.py', '').replace('.js', '').replace('.ts', '')

                if module in proc_file or proc_normalized in module:
                    dependencies.append(proc_file)
                    break

        return dependencies

    def _get_dependents(
        self,
        file_path: str,
        dep_graph: Dict,
        all_files: List[str]
    ) -> List[str]:
        """
        Get list of files that depend on this file.

        Args:
            file_path: Target file
            dep_graph: Dependency graph
            all_files: All files being refactored

        Returns:
            List of file paths that depend on this file
        """
        dependents = []
        file_normalized = file_path.replace('/', '.').replace('\\', '.').replace('.py', '').replace('.js', '').replace('.ts', '')

        for other_file in all_files:
            if other_file == file_path:
                continue

            # Check if other_file imports from file_path
            imports = dep_graph.get('imports', {}).get(other_file, [])
            for imp in imports:
                module = imp.get('module', '')

                if module in file_path or file_normalized in module:
                    dependents.append(other_file)
                    break

        return dependents

    def _generate_reason(
        self,
        file_path: str,
        dependencies: List[str],
        dependents: List[str],
        position: int,
        total: int
    ) -> str:
        """Generate a human-readable reason for this file's position in the plan."""
        if position == 1:
            if not dependencies:
                return "No dependencies - safe to refactor first"
            else:
                return "Foundation file - others depend on this"

        elif position == total:
            if dependencies:
                return f"Depends on {len(dependencies)} other file(s) - refactor last"
            else:
                return "Independent file - refactoring last"

        else:
            if dependencies and not dependents:
                return f"Leaf file - depends on {len(dependencies)} file(s)"
            elif not dependencies and dependents:
                return f"Core file - {len(dependents)} file(s) depend on this"
            elif dependencies and dependents:
                return f"Bridge file - links {len(dependencies)} dependencies to {len(dependents)} dependents"
            else:
                return "Independent file"

    def export_plan(self, plan: List[RefactorStep], output_path: str):
        """
        Export the refactoring plan to a file.

        Args:
            plan: List of RefactorStep objects
            output_path: Path to save the plan
        """
        import json

        plan_data = []
        for step in plan:
            plan_data.append({
                'step': step.step_number,
                'file': step.file_path,
                'description': step.description,
                'dependencies': step.dependencies,
                'dependents': step.dependents,
                'risk': step.risk_level,
                'impact': step.estimated_impact,
                'reason': step.reason
            })

        with open(output_path, 'w') as f:
            json.dump(plan_data, f, indent=2)

        click.echo(f"{Fore.GREEN}Plan exported to {output_path}{Style.RESET_ALL}")
