"""Diff manager for displaying code changes and managing backups."""

import difflib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


class DiffManager:
    """Manages code diffs and backups."""

    def __init__(self, create_backups: bool = True):
        """Initialize diff manager.

        Args:
            create_backups: Whether to create backup files
        """
        self.create_backups = create_backups

    def create_backup(self, filepath: str) -> Optional[str]:
        """Create a backup of the original file.

        Args:
            filepath: Path to file to backup

        Returns:
            Path to backup file, or None if backups disabled
        """
        if not self.create_backups:
            return None

        file_path = Path(filepath)
        if not file_path.exists():
            return None

        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"

        shutil.copy2(file_path, backup_path)
        return str(backup_path)

    def generate_diff(
        self,
        original: str,
        refactored: str,
        filepath: str,
        colored: bool = True
    ) -> str:
        """Generate a diff between original and refactored code.

        Args:
            original: Original code
            refactored: Refactored code
            filepath: Path to file (for context)
            colored: Whether to use colored output

        Returns:
            Formatted diff string
        """
        original_lines = original.splitlines(keepends=True)
        refactored_lines = refactored.splitlines(keepends=True)

        # Generate unified diff
        diff = difflib.unified_diff(
            original_lines,
            refactored_lines,
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
            lineterm=''
        )

        if colored:
            return self._colorize_diff(list(diff))
        else:
            return ''.join(diff)

    def _colorize_diff(self, diff_lines: list) -> str:
        """Add colors to diff output.

        Args:
            diff_lines: List of diff lines

        Returns:
            Colored diff string
        """
        colored_lines = []

        for line in diff_lines:
            if line.startswith('+++') or line.startswith('---'):
                colored_lines.append(Fore.CYAN + Style.BRIGHT + line)
            elif line.startswith('@@'):
                colored_lines.append(Fore.MAGENTA + Style.BRIGHT + line)
            elif line.startswith('+'):
                colored_lines.append(Fore.GREEN + line)
            elif line.startswith('-'):
                colored_lines.append(Fore.RED + line)
            else:
                colored_lines.append(line)

        return '\n'.join(colored_lines)

    def display_diff(
        self,
        original: str,
        refactored: str,
        filepath: str,
        colored: bool = True
    ):
        """Display diff to console.

        Args:
            original: Original code
            refactored: Refactored code
            filepath: Path to file
            colored: Whether to use colored output
        """
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 70}")
        print(f"DIFF: {filepath}")
        print(f"{'=' * 70}{Style.RESET_ALL}\n")

        diff = self.generate_diff(original, refactored, filepath, colored)
        print(diff)

        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 70}{Style.RESET_ALL}\n")

    def get_stats(self, original: str, refactored: str) -> dict:
        """Get statistics about the changes.

        Args:
            original: Original code
            refactored: Refactored code

        Returns:
            Dictionary with statistics
        """
        original_lines = original.splitlines()
        refactored_lines = refactored.splitlines()

        # Count changes
        diff = list(difflib.unified_diff(
            original_lines,
            refactored_lines,
            lineterm=''
        ))

        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        return {
            'original_lines': len(original_lines),
            'refactored_lines': len(refactored_lines),
            'lines_added': additions,
            'lines_removed': deletions,
            'net_change': len(refactored_lines) - len(original_lines)
        }

    def display_stats(self, stats: dict):
        """Display change statistics.

        Args:
            stats: Statistics dictionary from get_stats()
        """
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Change Statistics:{Style.RESET_ALL}")
        print(f"  Original lines:   {stats['original_lines']}")
        print(f"  Refactored lines: {stats['refactored_lines']}")
        print(f"  {Fore.GREEN}Lines added:      +{stats['lines_added']}{Style.RESET_ALL}")
        print(f"  {Fore.RED}Lines removed:    -{stats['lines_removed']}{Style.RESET_ALL}")

        net_change = stats['net_change']
        if net_change > 0:
            print(f"  Net change:       {Fore.GREEN}+{net_change}{Style.RESET_ALL}")
        elif net_change < 0:
            print(f"  Net change:       {Fore.RED}{net_change}{Style.RESET_ALL}")
        else:
            print(f"  Net change:       {net_change}")

    def save_refactored(self, filepath: str, refactored_code: str) -> bool:
        """Save refactored code to file.

        Args:
            filepath: Path to file
            refactored_code: Refactored code to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(refactored_code)
            return True
        except Exception as e:
            print(f"{Fore.RED}Error saving file: {e}{Style.RESET_ALL}")
            return False
