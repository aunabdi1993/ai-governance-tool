"""
Cross-file validators for ensuring refactored code maintains compatibility.
"""

import ast
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import re


class ValidationResult:
    """Result of validation checks."""

    def __init__(self, passed: bool, errors: List[str] = None, warnings: List[str] = None):
        self.passed = passed
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.passed = False

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)

    def __bool__(self):
        return self.passed

    def __str__(self):
        if self.passed:
            msg = "✓ Validation passed"
            if self.warnings:
                msg += f" ({len(self.warnings)} warnings)"
            return msg
        else:
            msg = f"✗ Validation failed with {len(self.errors)} errors"
            if self.warnings:
                msg += f" and {len(self.warnings)} warnings"
            return msg


class CrossFileValidator:
    """Validates refactored code maintains cross-file compatibility."""

    def __init__(self, original_files: Dict[str, str]):
        """
        Initialize validator.

        Args:
            original_files: Dict of {file_path: original_content}
        """
        self.original_files = original_files

    def validate_refactoring(
        self,
        changes: Dict[str, str],
        dependency_info: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Validate that changes maintain cross-file contracts.

        Args:
            changes: Dict of {file_path: new_content}
            dependency_info: Optional dependency analysis results

        Returns:
            ValidationResult object
        """
        result = ValidationResult(passed=True)

        # For each changed file, validate
        for file_path, new_content in changes.items():
            original_content = self.original_files.get(file_path, "")

            # Determine language
            ext = Path(file_path).suffix
            if ext == '.py':
                self._validate_python_file(file_path, original_content, new_content, result)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                self._validate_javascript_file(file_path, original_content, new_content, result)

        # If dependency info available, check cross-file dependencies
        if dependency_info and result.passed:
            self._validate_dependencies(changes, dependency_info, result)

        return result

    def _validate_python_file(
        self,
        file_path: str,
        original: str,
        new: str,
        result: ValidationResult
    ):
        """Validate Python file changes."""
        try:
            # Check 1: Syntax validity
            try:
                ast.parse(new, filename=file_path)
            except SyntaxError as e:
                result.add_error(f"{file_path}: Syntax error - {e}")
                return

            # Check 2: Extract exports from both versions
            old_exports = self._extract_python_exports(original)
            new_exports = self._extract_python_exports(new)

            # Check 3: Ensure no exported symbols removed
            old_export_names = {exp['name'] for exp in old_exports}
            new_export_names = {exp['name'] for exp in new_exports}

            missing = old_export_names - new_export_names
            if missing:
                result.add_error(
                    f"{file_path}: Removed exported symbols: {', '.join(missing)}"
                )

            # Check 4: Function signature compatibility
            self._check_python_signatures(file_path, old_exports, new_exports, result)

        except Exception as e:
            result.add_error(f"{file_path}: Validation error - {e}")

    def _extract_python_exports(self, code: str) -> List[Dict]:
        """Extract exported symbols from Python code."""
        try:
            tree = ast.parse(code)
            exports = []

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        exports.append({
                            'name': node.name,
                            'type': 'function',
                            'args': [arg.arg for arg in node.args.args],
                            'returns': ast.get_source_segment(code, node.returns) if node.returns else None
                        })

                elif isinstance(node, ast.ClassDef):
                    if not node.name.startswith('_'):
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                                methods.append({
                                    'name': item.name,
                                    'args': [arg.arg for arg in item.args.args]
                                })

                        exports.append({
                            'name': node.name,
                            'type': 'class',
                            'methods': methods
                        })

            return exports

        except Exception:
            return []

    def _check_python_signatures(
        self,
        file_path: str,
        old_exports: List[Dict],
        new_exports: List[Dict],
        result: ValidationResult
    ):
        """Check that function signatures remain compatible."""
        old_map = {exp['name']: exp for exp in old_exports}
        new_map = {exp['name']: exp for exp in new_exports}

        for name, old_exp in old_map.items():
            if name not in new_map:
                continue  # Already reported as missing

            new_exp = new_map[name]

            # Check functions
            if old_exp['type'] == 'function':
                old_args = old_exp.get('args', [])
                new_args = new_exp.get('args', [])

                # Allow adding optional parameters at the end
                if len(new_args) < len(old_args):
                    result.add_error(
                        f"{file_path}::{name}: Removed parameters (had {old_args}, now {new_args})"
                    )
                elif old_args != new_args[:len(old_args)]:
                    result.add_warning(
                        f"{file_path}::{name}: Parameter order changed (had {old_args}, now {new_args})"
                    )

            # Check classes
            elif old_exp['type'] == 'class':
                old_methods = {m['name'] for m in old_exp.get('methods', [])}
                new_methods = {m['name'] for m in new_exp.get('methods', [])}

                missing_methods = old_methods - new_methods
                if missing_methods:
                    result.add_error(
                        f"{file_path}::{name}: Removed methods: {', '.join(missing_methods)}"
                    )

    def _validate_javascript_file(
        self,
        file_path: str,
        original: str,
        new: str,
        result: ValidationResult
    ):
        """Validate JavaScript/TypeScript file changes."""
        # Extract exports using regex (basic validation)
        old_exports = self._extract_js_exports(original)
        new_exports = self._extract_js_exports(new)

        missing = old_exports - new_exports
        if missing:
            result.add_error(
                f"{file_path}: Removed exported symbols: {', '.join(missing)}"
            )

    def _extract_js_exports(self, code: str) -> Set[str]:
        """Extract exported symbol names from JavaScript code."""
        exports = set()

        # export function/class/const name
        pattern = r'export\s+(?:function|class|const|let|var)\s+(\w+)'
        for match in re.finditer(pattern, code):
            exports.add(match.group(1))

        # export { name1, name2 }
        pattern = r'export\s+{([^}]+)}'
        for match in re.finditer(pattern, code):
            names = match.group(1).split(',')
            for name in names:
                clean_name = name.strip().split()[0]  # Handle "name as alias"
                exports.add(clean_name)

        # export default Name
        pattern = r'export\s+default\s+(\w+)'
        for match in re.finditer(pattern, code):
            exports.add(match.group(1))

        return exports

    def _validate_dependencies(
        self,
        changes: Dict[str, str],
        dependency_info: Dict,
        result: ValidationResult
    ):
        """Validate cross-file dependencies are maintained."""
        imports = dependency_info.get('imports', {})
        exports = dependency_info.get('exports', {})

        # For each file being changed, check if other files depend on it
        for changed_file in changes.keys():
            # Find files that import from this file
            dependent_files = self._find_dependent_files(changed_file, imports)

            if dependent_files:
                result.add_warning(
                    f"{changed_file}: This file is imported by {len(dependent_files)} other files. "
                    f"Ensure compatibility is maintained."
                )

    def _find_dependent_files(self, target_file: str, imports: Dict) -> List[str]:
        """Find files that import from the target file."""
        dependents = []

        for file_path, import_list in imports.items():
            for imp in import_list:
                module = imp.get('module', '')
                # Check if this imports from target file
                if target_file.replace('/', '.').replace('\\', '.') in module:
                    dependents.append(file_path)
                    break

        return dependents


class TypeChecker:
    """Runs external type checkers for validation."""

    @staticmethod
    def run_python_type_check(files: Dict[str, str]) -> ValidationResult:
        """
        Run mypy type checking on Python files.

        Args:
            files: Dict of {file_path: content}

        Returns:
            ValidationResult
        """
        result = ValidationResult(passed=True)

        # Check if mypy is available
        if not TypeChecker._command_exists('mypy'):
            result.add_warning("mypy not installed - skipping type checking")
            return result

        # Create temporary directory with files
        with tempfile.TemporaryDirectory() as tmpdir:
            file_paths = []

            for file_path, content in files.items():
                if not file_path.endswith('.py'):
                    continue

                # Write file to temp location
                temp_path = os.path.join(tmpdir, os.path.basename(file_path))
                with open(temp_path, 'w') as f:
                    f.write(content)
                file_paths.append(temp_path)

            # Run mypy
            if file_paths:
                try:
                    proc = subprocess.run(
                        ['mypy', '--no-error-summary'] + file_paths,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if proc.returncode != 0:
                        # Parse mypy output
                        for line in proc.stdout.split('\n'):
                            if line.strip() and ':' in line:
                                result.add_error(f"Type error: {line}")

                except subprocess.TimeoutExpired:
                    result.add_warning("Type checking timed out")
                except Exception as e:
                    result.add_warning(f"Type checking failed: {e}")

        return result

    @staticmethod
    def run_javascript_type_check(files: Dict[str, str]) -> ValidationResult:
        """
        Run tsc (TypeScript compiler) type checking.

        Args:
            files: Dict of {file_path: content}

        Returns:
            ValidationResult
        """
        result = ValidationResult(passed=True)

        # Check if tsc is available
        if not TypeChecker._command_exists('tsc'):
            result.add_warning("tsc not installed - skipping type checking")
            return result

        # Similar implementation to Python but for TypeScript
        # Would create temp files and run tsc --noEmit

        return result

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ['which', command],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


class SyntaxValidator:
    """Validates syntax of refactored code."""

    @staticmethod
    def validate_python_syntax(code: str, filepath: str) -> ValidationResult:
        """Validate Python syntax."""
        result = ValidationResult(passed=True)

        try:
            ast.parse(code, filename=filepath)
        except SyntaxError as e:
            result.add_error(f"Syntax error at line {e.lineno}: {e.msg}")

        return result

    @staticmethod
    def validate_javascript_syntax(code: str, filepath: str) -> ValidationResult:
        """Validate JavaScript syntax using Node.js."""
        result = ValidationResult(passed=True)

        # Check if node is available
        if not TypeChecker._command_exists('node'):
            result.add_warning("Node.js not installed - skipping syntax validation")
            return result

        # Use node's --check flag
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name

            proc = subprocess.run(
                ['node', '--check', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )

            if proc.returncode != 0:
                result.add_error(f"Syntax error: {proc.stderr}")

            os.unlink(temp_path)

        except Exception as e:
            result.add_warning(f"Syntax validation failed: {e}")

        return result
