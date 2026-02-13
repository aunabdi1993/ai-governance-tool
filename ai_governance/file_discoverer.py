"""
File Discovery Module for AI Governance Tool.

Handles finding and filtering files for bulk refactoring operations.
"""

import os
from pathlib import Path
from typing import List, Set
import fnmatch


class FileDiscoverer:
    """Discovers files for bulk refactoring operations."""

    def __init__(self, supported_extensions: Set[str] = None):
        """
        Initialize FileDiscoverer.

        Args:
            supported_extensions: Set of supported file extensions (e.g., {'.py', '.js'})
                                If None, all common programming language files are supported.
        """
        if supported_extensions is None:
            # Import here to avoid circular imports
            from .language_config import get_all_extensions
            self.supported_extensions = get_all_extensions()
        else:
            self.supported_extensions = supported_extensions

    def discover_files(self, paths: List[str], recursive: bool = True,
                       pattern: str = None) -> List[Path]:
        """
        Discover files from given paths.

        Args:
            paths: List of file paths or directory paths
            recursive: Whether to search directories recursively
            pattern: Optional glob pattern to filter files (e.g., "test_*.py")

        Returns:
            List of Path objects for discovered files
        """
        discovered_files = []

        for path_str in paths:
            path = Path(path_str).resolve()

            if not path.exists():
                print(f"Warning: Path does not exist: {path}")
                continue

            if path.is_file():
                # Single file
                if self._is_supported_file(path, pattern):
                    discovered_files.append(path)
            elif path.is_dir():
                # Directory - discover files within it
                discovered_files.extend(
                    self._discover_in_directory(path, recursive, pattern)
                )

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in discovered_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)

        return unique_files

    def _discover_in_directory(self, directory: Path, recursive: bool,
                                pattern: str = None) -> List[Path]:
        """
        Discover files within a directory.

        Args:
            directory: Directory path to search
            recursive: Whether to search recursively
            pattern: Optional glob pattern to filter files

        Returns:
            List of discovered file paths
        """
        files = []

        if recursive:
            # Recursive search
            for root, _, filenames in os.walk(directory):
                root_path = Path(root)
                for filename in filenames:
                    file_path = root_path / filename
                    if self._is_supported_file(file_path, pattern):
                        files.append(file_path)
        else:
            # Non-recursive search (only immediate children)
            for item in directory.iterdir():
                if item.is_file() and self._is_supported_file(item, pattern):
                    files.append(item)

        return files

    def _is_supported_file(self, file_path: Path, pattern: str = None) -> bool:
        """
        Check if a file is supported for refactoring.

        Args:
            file_path: Path to the file
            pattern: Optional glob pattern to match against filename

        Returns:
            True if file is supported, False otherwise
        """
        # Check extension
        if file_path.suffix not in self.supported_extensions:
            return False

        # Check pattern if provided
        if pattern and not fnmatch.fnmatch(file_path.name, pattern):
            return False

        # Skip hidden files and __pycache__ directories
        if any(part.startswith('.') or part == '__pycache__'
               for part in file_path.parts):
            return False

        return True

    def group_by_directory(self, files: List[Path]) -> dict:
        """
        Group files by their parent directory.

        Args:
            files: List of file paths

        Returns:
            Dictionary mapping directory paths to lists of files
        """
        groups = {}
        for file_path in files:
            parent = file_path.parent
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(file_path)
        return groups
