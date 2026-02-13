"""Policy engine for loading and managing security policies."""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fnmatch import fnmatch
try:
    from importlib.resources import files
except ImportError:
    # Python < 3.9
    from importlib_resources import files


class PolicyEngine:
    """Manages security policies for AI governance."""

    def __init__(self, policy_path: Optional[str] = None):
        """Initialize policy engine with a policy file.

        Args:
            policy_path: Path to YAML policy file. Defaults to profiles/default-secure.yaml
        """
        if policy_path is None:
            # Use package resources to find the default policy file
            try:
                pkg_files = files('ai_governance')
                policy_path = pkg_files / 'profiles' / 'default-secure.yaml'
            except Exception:
                # Fallback for development environment
                policy_path = Path(__file__).parent / "profiles" / "default-secure.yaml"

        self.policy_path = Path(policy_path)
        self.policy = self._load_policy()
        self._compile_patterns()

    def _load_policy(self) -> Dict:
        """Load policy from YAML file."""
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found: {self.policy_path}")

        with open(self.policy_path, 'r') as f:
            policy = yaml.safe_load(f)

        return policy

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_patterns = {}

        for pattern_name, pattern_info in self.policy.get('sensitive_patterns', {}).items():
            try:
                self.compiled_patterns[pattern_name] = {
                    'regex': re.compile(pattern_info['pattern'], re.IGNORECASE),
                    'description': pattern_info['description'],
                    'severity': pattern_info.get('severity', 'medium')
                }
            except re.error as e:
                print(f"Warning: Invalid regex pattern for {pattern_name}: {e}")

    def is_file_blocked(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """Check if a file path matches any blocked patterns.

        Args:
            filepath: Path to check

        Returns:
            Tuple of (is_blocked, reason)
        """
        blocked_patterns = self.policy.get('blocked_file_patterns', [])

        for pattern in blocked_patterns:
            if fnmatch(filepath, pattern):
                return True, f"File path matches blocked pattern: {pattern}"

        return False, None

    def scan_content(self, content: str) -> List[Dict]:
        """Scan content for sensitive patterns.

        Args:
            content: Text content to scan

        Returns:
            List of findings with pattern name, description, severity, and matches
        """
        findings = []

        for pattern_name, pattern_data in self.compiled_patterns.items():
            matches = pattern_data['regex'].findall(content)

            if matches:
                # Redact matches for logging (show only first few chars)
                redacted_matches = [
                    match[:10] + "..." if len(match) > 10 else match
                    for match in matches[:3]  # Show max 3 examples
                ]

                findings.append({
                    'pattern': pattern_name,
                    'description': pattern_data['description'],
                    'severity': pattern_data['severity'],
                    'match_count': len(matches),
                    'examples': redacted_matches
                })

        return findings

    def get_cost_limits(self) -> Dict:
        """Get cost limit settings."""
        return self.policy.get('cost_limits', {})

    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled."""
        return self.policy.get('logging', {}).get('enabled', True)

    def get_policy_info(self) -> Dict:
        """Get policy metadata."""
        return {
            'name': self.policy.get('name', 'unknown'),
            'version': self.policy.get('version', 'unknown'),
            'description': self.policy.get('description', ''),
            'blocked_patterns_count': len(self.policy.get('blocked_file_patterns', [])),
            'sensitive_patterns_count': len(self.policy.get('sensitive_patterns', {}))
        }
