"""Scanner module for checking files against security policies."""

from pathlib import Path
from typing import Dict, List, Optional
from .policy_engine import PolicyEngine
from .core.base import SecurityScanner
from .core.types import ScanResult, Finding, SeverityLevel


class Scanner(SecurityScanner):
    """Scans files for security policy violations before AI processing.

    Implements the SecurityScanner abstract base class with PolicyEngine integration.
    """

    def __init__(self, policy_engine: PolicyEngine):
        """Initialize scanner with a policy engine.

        Args:
            policy_engine: PolicyEngine instance to use for scanning
        """
        self.policy_engine = policy_engine

    def scan_file(self, filepath: str) -> ScanResult:
        """Scan a file for policy violations.

        Args:
            filepath: Path to file to scan

        Returns:
            ScanResult indicating whether file is allowed, with findings

        Raises:
            ScanError: If the file cannot be read or scanned (captured in error field)
        """
        file_path = Path(filepath)

        # Check if file exists
        if not file_path.exists():
            return ScanResult(
                allowed=False,
                reason=f"File not found: {filepath}",
                findings=[],
                file_size=0,
                error=True,
                content=None
            )

        # Check if it's a file (not directory)
        if not file_path.is_file():
            return ScanResult(
                allowed=False,
                reason=f"Not a file: {filepath}",
                findings=[],
                file_size=0,
                error=True,
                content=None
            )

        # Get file size
        file_size = file_path.stat().st_size

        # Check file path patterns
        is_blocked, block_reason = self.policy_engine.is_file_blocked(str(file_path))
        if is_blocked:
            return ScanResult(
                allowed=False,
                reason=block_reason or "File path blocked by policy",
                findings=[],
                file_size=file_size,
                error=False,
                content=None
            )

        # Read and scan file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return ScanResult(
                allowed=False,
                reason="File is not a valid text file (binary content detected)",
                findings=[],
                file_size=file_size,
                error=True,
                content=None
            )
        except Exception as e:
            return ScanResult(
                allowed=False,
                reason=f"Error reading file: {str(e)}",
                findings=[],
                file_size=file_size,
                error=True,
                content=None
            )

        # Scan content for sensitive patterns
        findings = self.policy_engine.scan_content(content)

        if findings:
            # Build detailed reason
            critical_findings = [f for f in findings if f.severity == SeverityLevel.CRITICAL]
            high_findings = [f for f in findings if f.severity == SeverityLevel.HIGH]

            reason_parts = []
            if critical_findings:
                patterns = ', '.join([f.pattern for f in critical_findings])
                reason_parts.append(f"Critical: {patterns}")
            if high_findings:
                patterns = ', '.join([f.pattern for f in high_findings])
                reason_parts.append(f"High: {patterns}")

            reason = "Sensitive content detected - " + "; ".join(reason_parts)

            return ScanResult(
                allowed=False,
                reason=reason,
                findings=findings,
                file_size=file_size,
                error=False,
                content=content
            )

        # File passed all checks
        return ScanResult(
            allowed=True,
            reason="No policy violations detected",
            findings=[],
            file_size=file_size,
            error=False,
            content=content
        )

    def format_scan_result(self, scan_result: ScanResult, filepath: str) -> str:
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

        if scan_result.error:
            lines.append(f"❌ ERROR: {scan_result.reason}")
            return "\n".join(lines)

        if scan_result.allowed:
            lines.append(f"✅ ALLOWED: {scan_result.reason}")
            lines.append(f"File size: {scan_result.file_size} bytes")
        else:
            lines.append(f"🚫 BLOCKED: {scan_result.reason}")
            lines.append(f"File size: {scan_result.file_size} bytes")

            if scan_result.findings:
                lines.append("\nSensitive patterns detected:")
                for finding in scan_result.findings:
                    lines.append(f"  • {finding.pattern} ({finding.severity.value}): "
                                 f"{finding.description}")
                    lines.append(f"    Matches: {finding.match_count}, "
                                 f"Examples: {', '.join(finding.examples)}")

        return "\n".join(lines)
