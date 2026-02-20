"""Custom exception hierarchy for AI Governance Tool.

All exceptions derive from AIGovernanceError, enabling callers to
catch the entire hierarchy with a single except clause.

Example:
    >>> from ai_governance.core.exceptions import PolicyViolationError
    >>> try:
    ...     raise PolicyViolationError("File matched blocked pattern: **/secrets/**")
    ... except AIGovernanceError as e:
    ...     print(f"Governance error: {e}")
"""

from __future__ import annotations

from typing import Any, Optional


class AIGovernanceError(Exception):
    """Base exception for all AI Governance Tool errors.

    All custom exceptions in this package inherit from this class,
    enabling broad exception handling when required.

    Attributes:
        message: Human-readable error description.
        details: Optional additional context (e.g., file path, pattern).
    """

    def __init__(self, message: str, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


# ─── Configuration errors ─────────────────────────────────────────────────────


class ConfigError(AIGovernanceError):
    """Raised when configuration loading or validation fails.

    Example:
        >>> raise ConfigError("Policy file not found", details="/path/to/policy.yaml")
    """


# ─── Governance / policy errors ───────────────────────────────────────────────


class PolicyViolationError(AIGovernanceError):
    """Raised when a file matches a blocked file-path pattern.

    Attributes:
        filepath: The file path that triggered the violation.
        pattern: The blocking glob pattern.

    Example:
        >>> raise PolicyViolationError(
        ...     "File blocked by policy",
        ...     details={"filepath": "config/secrets.yaml", "pattern": "**/secrets/**"},
        ... )
    """

    def __init__(
        self,
        message: str,
        filepath: Optional[str] = None,
        pattern: Optional[str] = None,
    ) -> None:
        super().__init__(message, details={"filepath": filepath, "pattern": pattern})
        self.filepath = filepath
        self.pattern = pattern


class SecurityViolationError(AIGovernanceError):
    """Raised when sensitive content is detected in a file.

    Attributes:
        filepath: The scanned file path.
        findings: List of Finding dicts describing detected patterns.

    Example:
        >>> raise SecurityViolationError(
        ...     "Sensitive content detected",
        ...     filepath="user_service.py",
        ...     findings=[{"pattern": "api_keys", "severity": "critical", ...}],
        ... )
    """

    def __init__(
        self,
        message: str,
        filepath: Optional[str] = None,
        findings: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message, details={"filepath": filepath, "findings": findings})
        self.filepath = filepath
        self.findings = findings or []


# ─── Provider errors ──────────────────────────────────────────────────────────


class ProviderError(AIGovernanceError):
    """Base class for AI provider errors.

    Attributes:
        provider: Name of the provider that raised the error.
        status_code: HTTP status code, if applicable.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message, details={"provider": provider, "status_code": status_code})
        self.provider = provider
        self.status_code = status_code


class ProviderAuthError(ProviderError):
    """Raised when API authentication fails (invalid or missing key).

    Example:
        >>> raise ProviderAuthError("Invalid API key", provider="claude")
    """


class ProviderRateLimitError(ProviderError):
    """Raised when the provider rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Suggested wait time in seconds, if provided by the API.

    Example:
        >>> raise ProviderRateLimitError("Rate limit exceeded", provider="claude", retry_after=30)
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message, provider=provider, status_code=429)
        self.retry_after = retry_after


class ProviderQuotaError(ProviderError):
    """Raised when the account quota / credits are exhausted.

    Example:
        >>> raise ProviderQuotaError("Account quota exceeded", provider="openai")
    """


class ProviderTimeoutError(ProviderError):
    """Raised when a provider API call times out.

    Example:
        >>> raise ProviderTimeoutError("Request timed out after 30s", provider="claude")
    """


class ProviderUnavailableError(ProviderError):
    """Raised when the provider API is temporarily unavailable (HTTP 529).

    Example:
        >>> raise ProviderUnavailableError("API overloaded", provider="claude", status_code=529)
    """


# ─── Audit errors ─────────────────────────────────────────────────────────────


class AuditError(AIGovernanceError):
    """Raised when audit logging fails.

    Example:
        >>> raise AuditError("Failed to write audit entry", details={"db_path": "/tmp/audit.db"})
    """


# ─── Scan errors ──────────────────────────────────────────────────────────────


class ScanError(AIGovernanceError):
    """Raised when a file cannot be scanned (e.g., binary file, read error).

    Attributes:
        filepath: The file that could not be scanned.

    Example:
        >>> raise ScanError("Cannot read binary file", filepath="assets/logo.png")
    """

    def __init__(self, message: str, filepath: Optional[str] = None) -> None:
        super().__init__(message, details={"filepath": filepath})
        self.filepath = filepath
