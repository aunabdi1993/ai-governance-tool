"""Runs tests to validate refactored code."""

import subprocess
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .validators import ValidationResult


class TestRunner:
    """Runs project tests to validate refactoring."""

    def __init__(self, project_root: str = "."):
        """
        Initialize test runner.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.test_framework = self._detect_test_framework()

    def _detect_test_framework(self) -> Optional[str]:
        """
        Auto-detect test framework being used.

        Returns:
            Framework name or None if not detected
        """
        # Check for pytest
        if (Path(self.project_root) / "pytest.ini").exists() or \
           (Path(self.project_root) / "pyproject.toml").exists():
            if self._command_exists("pytest"):
                return "pytest"

        # Check for unittest (Python)
        if (Path(self.project_root) / "tests").exists() or \
           (Path(self.project_root) / "test").exists():
            return "unittest"

        # Check for npm/jest (JavaScript/TypeScript)
        package_json = Path(self.project_root) / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get('scripts', {})
                    if 'test' in scripts:
                        return "npm"
            except:
                pass

        # Check for Go tests
        if list(Path(self.project_root).glob("*_test.go")):
            if self._command_exists("go"):
                return "go"

        # Check for Rust tests
        if (Path(self.project_root) / "Cargo.toml").exists():
            if self._command_exists("cargo"):
                return "cargo"

        return None

    def run_tests(
        self,
        test_files: Optional[List[str]] = None,
        timeout: int = 300,
        capture_output: bool = True
    ) -> ValidationResult:
        """
        Run tests to validate code changes.

        Args:
            test_files: Specific test files to run, or None for all tests
            timeout: Maximum time to wait for tests (seconds)
            capture_output: If True, capture test output

        Returns:
            ValidationResult with test outcomes
        """
        result = ValidationResult(passed=True)

        if not self.test_framework:
            result.add_warning("No test framework detected - skipping test validation")
            return result

        try:
            # Build command based on framework
            cmd = self._build_test_command(test_files)

            if not cmd:
                result.add_warning(f"Could not build test command for {self.test_framework}")
                return result

            # Run tests
            proc = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )

            # Parse results
            if proc.returncode == 0:
                # All tests passed
                test_count = self._count_tests(proc.stdout + proc.stderr)
                if test_count > 0:
                    result.add_warning(f"✓ All {test_count} test(s) passed")
                else:
                    result.add_warning("✓ Tests completed successfully")
            else:
                # Some tests failed
                failures = self._parse_test_failures(proc.stdout + proc.stderr)

                if failures:
                    for failure in failures[:10]:  # Limit to 10 failures
                        result.add_error(failure)
                else:
                    result.add_error(f"Tests failed with exit code {proc.returncode}")

        except subprocess.TimeoutExpired:
            result.add_error(f"Test suite timed out after {timeout} seconds")
        except FileNotFoundError:
            result.add_error(f"Test command not found: {cmd[0]}")
        except Exception as e:
            result.add_warning(f"Could not run tests: {e}")

        return result

    def _build_test_command(self, test_files: Optional[List[str]] = None) -> Optional[List[str]]:
        """
        Build test command based on detected framework.

        Args:
            test_files: Specific test files to run

        Returns:
            Command as list of strings, or None if unable to build
        """
        if self.test_framework == "pytest":
            cmd = ["pytest", "-v", "--tb=short", "--color=yes"]
            if test_files:
                cmd.extend(test_files)
            return cmd

        elif self.test_framework == "unittest":
            cmd = ["python", "-m", "unittest", "discover"]
            if test_files:
                # unittest discover doesn't support specific files well
                # Fall back to running each file
                return ["python", "-m", "unittest"] + test_files
            return cmd

        elif self.test_framework == "npm":
            return ["npm", "test"]

        elif self.test_framework == "go":
            cmd = ["go", "test", "-v"]
            if test_files:
                cmd.extend(test_files)
            else:
                cmd.append("./...")
            return cmd

        elif self.test_framework == "cargo":
            return ["cargo", "test", "--color=always"]

        return None

    def _parse_test_failures(self, output: str) -> List[str]:
        """
        Parse test output to extract failure messages.

        Args:
            output: Combined stdout and stderr from test run

        Returns:
            List of failure messages
        """
        failures = []
        lines = output.split('\n')

        if self.test_framework == "pytest":
            # Look for FAILED markers
            for line in lines:
                if 'FAILED' in line or 'ERROR' in line:
                    failures.append(line.strip())

            # Also look for assertion errors
            in_failure = False
            failure_lines = []
            for line in lines:
                if 'FAILED' in line or '_ _ _' in line:
                    in_failure = True
                    failure_lines = [line.strip()]
                elif in_failure:
                    if line.strip() and not line.startswith('='):
                        failure_lines.append(line.strip())
                    if 'AssertionError' in line or 'Error:' in line:
                        failures.append(' '.join(failure_lines[-3:]))
                        in_failure = False

        elif self.test_framework in ["unittest", "npm"]:
            # Look for FAIL or ERROR
            for line in lines:
                if 'FAIL:' in line or 'ERROR:' in line or 'Error:' in line:
                    failures.append(line.strip())

        elif self.test_framework == "go":
            # Look for FAIL or panic
            for line in lines:
                if '--- FAIL:' in line or 'panic:' in line:
                    failures.append(line.strip())

        elif self.test_framework == "cargo":
            # Look for test result failures
            for line in lines:
                if 'test result: FAILED' in line or 'failures:' in line:
                    failures.append(line.strip())

        return failures[:10]  # Limit to first 10 failures

    def _count_tests(self, output: str) -> int:
        """
        Count number of tests from output.

        Args:
            output: Test output

        Returns:
            Number of tests run
        """
        if self.test_framework == "pytest":
            # Look for "X passed" or "X passed, Y warnings"
            import re
            match = re.search(r'(\d+) passed', output)
            if match:
                return int(match.group(1))

        elif self.test_framework == "unittest":
            # Look for "Ran X tests"
            import re
            match = re.search(r'Ran (\d+) test', output)
            if match:
                return int(match.group(1))

        elif self.test_framework == "go":
            # Count "--- PASS:" lines
            return output.count('--- PASS:')

        return 0

    def find_related_tests(self, file_path: str) -> List[str]:
        """
        Find test files related to a source file.

        Args:
            file_path: Source file path

        Returns:
            List of related test file paths
        """
        tests = []
        file_path_obj = Path(file_path)
        file_stem = file_path_obj.stem
        file_dir = file_path_obj.parent

        # Common test patterns
        test_patterns = [
            f"test_{file_stem}.py",
            f"{file_stem}_test.py",
            f"test_{file_stem}.js",
            f"{file_stem}.test.js",
            f"{file_stem}.test.ts",
            f"{file_stem}.test.tsx",
            f"{file_stem}.spec.js",
            f"{file_stem}.spec.ts",
            f"{file_stem}_test.go",
        ]

        # Search in common test directories
        test_dirs = [
            file_dir / "tests",
            file_dir / "test",
            file_dir / "__tests__",
            file_dir / "spec",
            Path(self.project_root) / "tests",
            Path(self.project_root) / "test",
            Path(self.project_root) / "__tests__",
        ]

        # Also check same directory as source file
        test_dirs.append(file_dir)

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            for pattern in test_patterns:
                test_file = test_dir / pattern
                if test_file.exists():
                    tests.append(str(test_file))

        return tests

    def run_related_tests(
        self,
        file_paths: List[str],
        timeout: int = 300
    ) -> ValidationResult:
        """
        Run tests related to specific source files.

        Args:
            file_paths: List of source file paths
            timeout: Maximum time for test execution

        Returns:
            ValidationResult with test outcomes
        """
        # Find all related test files
        all_test_files = set()
        for file_path in file_paths:
            related = self.find_related_tests(file_path)
            all_test_files.update(related)

        if not all_test_files:
            result = ValidationResult(passed=True)
            result.add_warning("No related test files found")
            return result

        # Run the related tests
        return self.run_tests(test_files=list(all_test_files), timeout=timeout)

    def _command_exists(self, cmd: str) -> bool:
        """
        Check if command exists in PATH.

        Args:
            cmd: Command name

        Returns:
            True if command exists
        """
        try:
            subprocess.run(
                ['which', cmd],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def get_test_coverage(self) -> Optional[Dict]:
        """
        Get test coverage information if available.

        Returns:
            Dict with coverage info, or None if not available
        """
        # Check for pytest-cov
        if self.test_framework == "pytest" and self._command_exists("pytest"):
            try:
                proc = subprocess.run(
                    ["pytest", "--cov", "--cov-report=json", "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=self.project_root
                )

                coverage_file = Path(self.project_root) / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        return json.load(f)
            except:
                pass

        return None
