"""Core module for AI Governance Tool.

Contains the exception hierarchy, shared types, and abstract base classes
that form the foundation of the system's architecture.
"""

from .exceptions import (
    AIGovernanceError,
    ConfigError,
    PolicyViolationError,
    SecurityViolationError,
    ProviderError,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderQuotaError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    AuditError,
    ScanError,
)
from .types import (
    ScanResult,
    RefactorResult,
    AuditEntry,
    PolicyInfo,
    CostEstimate,
    TokenUsage,
    Finding,
    SeverityLevel,
    OperationStatus,
    ProviderName,
)
from .base import (
    AIProvider,
    GovernanceEngine,
    SecurityScanner,
    BaseAuditLogger,
    BaseConfigManager,
)

__all__ = [
    # Exceptions
    "AIGovernanceError",
    "ConfigError",
    "PolicyViolationError",
    "SecurityViolationError",
    "ProviderError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderQuotaError",
    "ProviderTimeoutError",
    "ProviderUnavailableError",
    "AuditError",
    "ScanError",
    # Types
    "ScanResult",
    "RefactorResult",
    "AuditEntry",
    "PolicyInfo",
    "CostEstimate",
    "TokenUsage",
    "Finding",
    "SeverityLevel",
    "OperationStatus",
    "ProviderName",
    # Base classes
    "AIProvider",
    "GovernanceEngine",
    "SecurityScanner",
    "BaseAuditLogger",
    "BaseConfigManager",
]
