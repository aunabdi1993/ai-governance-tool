"""Scanner module for checking files against security policies."""

from pathlib import Path
from typing import Dict, Tuple
from .policy_engine import PolicyEngine


class Scanner:
    """Scans files for security policy violations before AI processing."""

    def __init__(self, policy_engine: PolicyEngine):
        """Initialize scanner with a policy engine.

        Args:
            policy_engine: PolicyEngine instance to use for scanning
        """
        self.policy_engine = policy_engine

    def scan_file(self, filepath: str) -> Dict:
        """Scan a file for policy violations.

        Args:
            filepath: Path to file to scan

        Returns:
            Dictionary with scan results including:
            - allowed: bool
            - reason: str
            - findings: list of detected sensitive patterns
            - file_size: int
        """
        file_path = Path(filepath)

        # Check if file exists
        if not file_path.exists():
            return {
                'allowed': False,
                'reason': f"File not found: {filepath}",
                'findings': [],
                'file_size': 0,
                'error': True
            }

        # Check if it's a file (not directory)
        if not file_path.is_file():
            return {
                'allowed': False,
                'reason': f"Not a file: {filepath}",
                'findings': [],
                'file_size': 0,
                'error': True
            }

        # Get file size
        file_size = file_path.stat().st_size

        # Check file path patterns
        is_blocked, block_reason = self.policy_engine.is_file_blocked(str(file_path))
        if is_blocked:
            return {
                'allowed': False,
                'reason': block_reason,
                'findings': [],
                'file_size': file_size,
                'error': False
            }

        # Read and scan file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return {
                'allowed': False,
                'reason': "File is not a valid text file (binary content detected)",
                'findings': [],
                'file_size': file_size,
                'error': True
            }
        except Exception as e:
            return {
                'allowed': False,
                'reason': f"Error reading file: {str(e)}",
                'findings': [],
                'file_size': file_size,
                'error': True
            }

        # Scan content for sensitive patterns
        findings = self.policy_engine.scan_content(content)

        if findings:
            # Build detailed reason
            critical_findings = [f for f in findings if f['severity'] == 'critical']
            high_findings = [f for f in findings if f['severity'] == 'high']

            reason_parts = []
            if critical_findings:
                patterns = ', '.join([f['pattern'] for f in critical_findings])
                reason_parts.append(f"Critical: {patterns}")
            if high_findings:
                patterns = ', '.join([f['pattern'] for f in high_findings])
                reason_parts.append(f"High: {patterns}")

            reason = "Sensitive content detected - " + "; ".join(reason_parts)

            return {
                'allowed': False,
                'reason': reason,
                'findings': findings,
                'file_size': file_size,
                'error': False,
                'content': content
            }

        # File passed all checks
        return {
            'allowed': True,
            'reason': "No policy violations detected",
            'findings': [],
            'file_size': file_size,
            'error': False,
            'content': content
        }

    def format_scan_result(self, scan_result: Dict, filepath: str) -> str:
        """Format scan results for display.

        Args:
            scan_result: Result from scan_file()
            filepath: Path to the scanned file

        Returns:
            Formatted string for display
        """
        lines = []
        lines.append(f"\nScan Results for: {filepath}")
        lines.append("-" * 60)

        if scan_result.get('error'):
            lines.append(f"❌ ERROR: {scan_result['reason']}")
            return "\n".join(lines)

        if scan_result['allowed']:
            lines.append(f"✅ ALLOWED: {scan_result['reason']}")
            lines.append(f"File size: {scan_result['file_size']} bytes")
        else:
            lines.append(f"🚫 BLOCKED: {scan_result['reason']}")
            lines.append(f"File size: {scan_result['file_size']} bytes")

            if scan_result['findings']:
                lines.append("\nSensitive patterns detected:")
                for finding in scan_result['findings']:
                    lines.append(f"  • {finding['pattern']} ({finding['severity']}): "
                                 f"{finding['description']}")
                    lines.append(f"    Matches: {finding['match_count']}, "
                                 f"Examples: {', '.join(finding['examples'])}")

        return "\n".join(lines)
