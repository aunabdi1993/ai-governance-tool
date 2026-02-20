"""Abstract base classes for AI Governance Tool.

Defines the contracts for all major components, enabling dependency injection,
testing with mocks, and easy extension to support new providers, policies,
scanners, loggers, and configuration systems.

Example:
    >>> from ai_governance.core.base import AIProvider
    >>> from ai_governance.core.types import RefactorResult, CostEstimate
    >>>
    >>> class MyCustomProvider(AIProvider):
    ...     def refactor_code(self, code: str, target: str, filepath: str) -> RefactorResult:
    ...         # Custom implementation
    ...         pass
    ...     # Implement other abstract methods...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    AuditEntry,
    CostEstimate,
    Finding,
    PolicyInfo,
    RefactorResult,
    ScanResult,
)


# ─── AI Provider ──────────────────────────────────────────────────────────────


class AIProvider(ABC):
    """Abstract base class for AI refactoring providers (Strategy pattern).

    Subclasses implement support for specific AI APIs (e.g., Claude, OpenAI).
    All providers must implement the core refactoring and cost estimation methods.

    Attributes:
        model: The model identifier (e.g., "claude-sonnet-4-5-20250929").
        api_key: API key for authentication.

    Example:
        >>> provider = ClaudeProvider(api_key="sk-...")
        >>> result = provider.refactor_code(code="def foo(): pass", target="add type hints", filepath="main.py")
        >>> print(result.success)
        True
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the AI provider.

        Args:
            api_key: API key for authentication.
            model: Model identifier (provider-specific default if None).
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def refactor_code(
        self,
        code: str,
        target_description: str,
        filepath: str,
    ) -> RefactorResult:
        """Refactor code using the AI provider.

        Args:
            code: Source code to refactor.
            target_description: Description of desired refactoring.
            filepath: Path to source file (for context).

        Returns:
            RefactorResult containing success status, refactored code, and usage stats.

        Raises:
            ProviderError: If the API call fails.
            ProviderAuthError: If authentication fails.
            ProviderRateLimitError: If rate limit is exceeded.
        """
        pass

    @abstractmethod
    def refactor_with_context(
        self,
        code: str,
        target_description: str,
        filepath: str,
        context_files: Optional[Dict[str, str]] = None,
        dependency_info: Optional[Dict[str, Any]] = None,
    ) -> RefactorResult:
        """Refactor code with awareness of related files and dependencies.

        Args:
            code: Source code to refactor.
            target_description: Description of desired refactoring.
            filepath: Path to source file.
            context_files: Dict of {file_path: file_content} for related files.
            dependency_info: Dependency analysis results with imports/exports.

        Returns:
            RefactorResult containing success status, refactored code, and usage stats.

        Raises:
            ProviderError: If the API call fails.
        """
        pass

    @abstractmethod
    def estimate_cost(self, code: str, target_description: str) -> CostEstimate:
        """Estimate the cost of refactoring without making the API call.

        Args:
            code: Source code.
            target_description: Refactoring target.

        Returns:
            CostEstimate with estimated tokens and cost.
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the provider and model.

        Returns:
            Dictionary with provider name, model ID, pricing, and capabilities.

        Example:
            >>> provider.get_model_info()
            {
                "provider": "claude",
                "model": "claude-sonnet-4-5-20250929",
                "input_price_per_1m": 3.0,
                "output_price_per_1m": 15.0,
                "max_tokens": 4096,
            }
        """
        pass


# ─── Governance Engine ────────────────────────────────────────────────────────


class GovernanceEngine(ABC):
    """Abstract base class for policy validation engines.

    Subclasses implement different policy mechanisms (e.g., YAML-based rules,
    database-backed policies, API-driven rules).

    Example:
        >>> engine = YAMLGovernanceEngine(policy_path="policy.yaml")
        >>> is_blocked, reason = engine.is_file_blocked("/path/to/secrets.yaml")
        >>> print(is_blocked)
        True
    """

    @abstractmethod
    def is_file_blocked(self, filepath: str) -> tuple[bool, Optional[str]]:
        """Check if a file path matches any blocked patterns.

        Args:
            filepath: Path to check.

        Returns:
            Tuple of (is_blocked, reason).

        Example:
            >>> is_blocked, reason = engine.is_file_blocked("config/secrets.yaml")
            >>> print(reason)
            "File path matches blocked pattern: **/secrets/**"
        """
        pass

    @abstractmethod
    def scan_content(self, content: str) -> List[Finding]:
        """Scan content for sensitive patterns.

        Args:
            content: Text content to scan.

        Returns:
            List of Finding objects describing detected patterns.

        Example:
            >>> findings = engine.scan_content("API_KEY=sk-1234567890")
            >>> print(findings[0].pattern)
            "api_keys"
        """
        pass

    @abstractmethod
    def get_policy_info(self) -> PolicyInfo:
        """Get metadata about the loaded policy.

        Returns:
            PolicyInfo with name, version, and pattern counts.
        """
        pass


# ─── Security Scanner ─────────────────────────────────────────────────────────


class SecurityScanner(ABC):
    """Abstract base class for file security scanners.

    Scanners coordinate between governance engines and file I/O to perform
    comprehensive security checks on files before AI processing.

    Example:
        >>> scanner = FileSecurityScanner(governance_engine)
        >>> result = scanner.scan_file("/path/to/file.py")
        >>> print(result.allowed)
        True
    """

    @abstractmethod
    def scan_file(self, filepath: str) -> ScanResult:
        """Scan a file for policy violations and sensitive content.

        Args:
            filepath: Path to file to scan.

        Returns:
            ScanResult indicating whether file is allowed, with findings.

        Raises:
            ScanError: If the file cannot be read or scanned.

        Example:
            >>> result = scanner.scan_file("user_service.py")
            >>> if not result.allowed:
            ...     print(f"Blocked: {result.reason}")
        """
        pass


# ─── Audit Logger ─────────────────────────────────────────────────────────────


class BaseAuditLogger(ABC):
    """Abstract base class for audit logging.

    Subclasses implement different storage backends (e.g., SQLite, PostgreSQL,
    JSON files, cloud logging services).

    Example:
        >>> logger = JSONAuditLogger(db_path="audit.db")
        >>> logger.log_action(
        ...     filepath="main.py",
        ...     action="refactor",
        ...     status=OperationStatus.SUCCESS,
        ...     tokens_used=1000,
        ...     cost=0.05,
        ... )
    """

    @abstractmethod
    def log_action(
        self,
        filepath: str,
        action: str,
        status: str,
        reason: Optional[str] = None,
        tokens_used: int = 0,
        cost: float = 0.0,
        findings: Optional[List[Finding]] = None,
        model: Optional[str] = None,
        target_description: Optional[str] = None,
        original_code: Optional[str] = None,
        refactored_code: Optional[str] = None,
        **kwargs: Any,
    ) -> int:
        """Log an action to the audit system.

        Args:
            filepath: Path to file being processed.
            action: Action type (refactor, scan, validate).
            status: Operation status (allowed, blocked, success, failed).
            reason: Reason for status.
            tokens_used: Number of tokens used.
            cost: Cost in USD.
            findings: List of security findings.
            model: AI model used.
            target_description: Refactoring target description.
            original_code: Original code before refactoring.
            refactored_code: Code after refactoring.
            **kwargs: Additional arbitrary metadata.

        Returns:
            Record ID of the logged entry.

        Raises:
            AuditError: If logging fails.
        """
        pass

    @abstractmethod
    def get_recent_logs(self, limit: int = 50) -> List[AuditEntry]:
        """Get recent audit logs.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of AuditEntry objects.
        """
        pass

    @abstractmethod
    def get_logs_by_status(self, status: str, limit: int = 50) -> List[AuditEntry]:
        """Get logs filtered by status.

        Args:
            status: Status to filter by (allowed, blocked, success, failed).
            limit: Maximum number of records to return.

        Returns:
            List of AuditEntry objects.
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics.

        Returns:
            Dictionary with total requests, tokens, cost, and status breakdown.

        Example:
            >>> stats = logger.get_statistics()
            >>> print(stats)
            {
                "total_requests": 42,
                "total_tokens": 12000,
                "total_cost": 0.42,
                "status_counts": {"success": 38, "blocked": 4},
                "recent_24h": 10,
            }
        """
        pass


# ─── Configuration Manager ────────────────────────────────────────────────────


class BaseConfigManager(ABC):
    """Abstract base class for configuration management.

    Subclasses implement different configuration backends (e.g., YAML files,
    environment variables, remote configuration services).

    Example:
        >>> manager = YAMLConfigManager()
        >>> policy_path = manager.find_config()
        >>> print(policy_path)
        "/path/to/.ai-governance/policy.yaml"
    """

    @abstractmethod
    def find_config(self, explicit_path: Optional[str] = None) -> str:
        """Find configuration file using priority hierarchy.

        Args:
            explicit_path: Path provided via --policy flag (highest priority).

        Returns:
            Path to configuration file to use.

        Raises:
            ConfigError: If no valid configuration is found.

        Example:
            >>> config_path = manager.find_config()
            >>> print(config_path)
            "./.ai-governance/policy.yaml"
        """
        pass

    @abstractmethod
    def init_project_config(self, template: str = "default-secure", force: bool = False) -> Path:
        """Initialize project-level configuration.

        Args:
            template: Template name to use.
            force: Overwrite existing configuration.

        Returns:
            Path to created configuration file.

        Raises:
            ConfigError: If initialization fails.
        """
        pass

    @abstractmethod
    def init_user_config(self, template: str = "default-secure", force: bool = False) -> Path:
        """Initialize user-level configuration.

        Args:
            template: Template name to use.
            force: Overwrite existing configuration.

        Returns:
            Path to created configuration file.

        Raises:
            ConfigError: If initialization fails.
        """
        pass
