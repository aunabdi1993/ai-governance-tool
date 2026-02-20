"""Shared type definitions and dataclasses for AI Governance Tool.

This module provides structured types used across the codebase, enabling
type checking with mypy and improving IDE auto-completion.

Example:
    >>> from ai_governance.core.types import ScanResult, Finding, SeverityLevel
    >>> finding = Finding(
    ...     pattern="api_keys",
    ...     description="API key detected",
    ...     severity=SeverityLevel.CRITICAL,
    ...     match_count=1,
    ...     examples=["sk-1234..."],
    ... )
    >>> scan_result = ScanResult(
    ...     allowed=False,
    ...     reason="Sensitive content detected",
    ...     findings=[finding],
    ...     file_size=1024,
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union


# ─── Enumerations ─────────────────────────────────────────────────────────────


class SeverityLevel(str, Enum):
    """Security finding severity levels.

    CRITICAL: Immediate security risk (e.g., API keys, private keys).
    HIGH: Significant security concern (e.g., passwords, tokens).
    MEDIUM: Potential security issue (e.g., emails, URLs with credentials).
    LOW: Minor security consideration.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OperationStatus(str, Enum):
    """Status of an operation (scan, refactor, validation).

    ALLOWED: File passed security checks.
    BLOCKED: File blocked by policy.
    SUCCESS: Operation completed successfully.
    FAILED: Operation failed due to an error.
    ERROR: Unexpected error occurred.
    PENDING: Operation is pending.
    IN_PROGRESS: Operation is currently running.
    """

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class ProviderName(str, Enum):
    """Supported AI provider names.

    CLAUDE: Anthropic's Claude models.
    OPENAI: OpenAI's GPT models.
    """

    CLAUDE = "claude"
    OPENAI = "openai"


# ─── Security scanning types ──────────────────────────────────────────────────


@dataclass
class Finding:
    """Represents a single security finding (sensitive pattern match).

    Attributes:
        pattern: Name of the detected pattern (e.g., "api_keys").
        description: Human-readable description of the pattern.
        severity: Severity level of the finding.
        match_count: Number of times the pattern was found.
        examples: Redacted examples of matches (for logging).
    """

    pattern: str
    description: str
    severity: SeverityLevel
    match_count: int
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to a dictionary."""
        return {
            "pattern": self.pattern,
            "description": self.description,
            "severity": self.severity.value,
            "match_count": self.match_count,
            "examples": self.examples,
        }


@dataclass
class ScanResult:
    """Result of scanning a file for security violations.

    Attributes:
        allowed: Whether the file is allowed to be processed.
        reason: Human-readable reason for allow/block decision.
        findings: List of security findings detected.
        file_size: Size of the file in bytes.
        error: Whether an error occurred during scanning.
        content: File content (populated if allowed=True).
    """

    allowed: bool
    reason: str
    findings: List[Finding] = field(default_factory=list)
    file_size: int = 0
    error: bool = False
    content: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert scan result to a dictionary."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "findings": [f.to_dict() for f in self.findings],
            "file_size": self.file_size,
            "error": self.error,
            "content": self.content,
        }


# ─── AI provider types ────────────────────────────────────────────────────────


@dataclass
class TokenUsage:
    """Token usage statistics for an AI API call.

    Attributes:
        input: Number of input tokens.
        output: Number of output tokens.
        total: Total tokens (input + output).
    """

    input: int
    output: int
    total: int

    def to_dict(self) -> Dict[str, int]:
        """Convert token usage to a dictionary."""
        return {"input": self.input, "output": self.output, "total": self.total}


@dataclass
class CostEstimate:
    """Cost estimation for an AI API call.

    Attributes:
        estimated_input_tokens: Estimated input tokens.
        estimated_output_tokens: Estimated output tokens.
        estimated_total_tokens: Total estimated tokens.
        estimated_cost: Estimated cost in USD.
    """

    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_total_tokens: int
    estimated_cost: float

    def to_dict(self) -> Dict[str, Union[int, float]]:
        """Convert cost estimate to a dictionary."""
        return {
            "estimated_input_tokens": self.estimated_input_tokens,
            "estimated_output_tokens": self.estimated_output_tokens,
            "estimated_total_tokens": self.estimated_total_tokens,
            "estimated_cost": self.estimated_cost,
        }


@dataclass
class RefactorResult:
    """Result of a code refactoring operation.

    Attributes:
        success: Whether the refactoring was successful.
        refactored_code: The refactored code (if successful).
        error: Error message (if failed).
        tokens_used: Token usage statistics.
        cost: Actual cost in USD.
        model: AI model used for refactoring.
    """

    success: bool
    refactored_code: Optional[str] = None
    error: Optional[str] = None
    tokens_used: Optional[TokenUsage] = None
    cost: float = 0.0
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert refactor result to a dictionary."""
        return {
            "success": self.success,
            "refactored_code": self.refactored_code,
            "error": self.error,
            "tokens_used": self.tokens_used.to_dict() if self.tokens_used else None,
            "cost": self.cost,
            "model": self.model,
        }


# ─── Audit logging types ──────────────────────────────────────────────────────


@dataclass
class AuditEntry:
    """Represents a single audit log entry.

    Attributes:
        id: Unique identifier for the entry (optional, set by database).
        timestamp: ISO 8601 timestamp of the operation.
        filepath: Path to the file being processed.
        action: Action type (refactor, scan, validate).
        status: Operation status (allowed, blocked, success, failed).
        reason: Reason for the status.
        tokens_used: Number of tokens used (0 for non-AI operations).
        cost: Cost in USD (0.0 for non-AI operations).
        findings: Security findings (list of Finding objects).
        model: AI model used (if applicable).
        target_description: Refactoring target description (if applicable).
        original_code: Original code before refactoring (optional).
        refactored_code: Code after refactoring (optional).
        metadata: Additional arbitrary metadata.
    """

    timestamp: str
    filepath: str
    action: str
    status: OperationStatus
    reason: Optional[str] = None
    tokens_used: int = 0
    cost: float = 0.0
    findings: List[Finding] = field(default_factory=list)
    model: Optional[str] = None
    target_description: Optional[str] = None
    original_code: Optional[str] = None
    refactored_code: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to a dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "filepath": self.filepath,
            "action": self.action,
            "status": self.status.value,
            "reason": self.reason,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "findings": [f.to_dict() for f in self.findings],
            "model": self.model,
            "target_description": self.target_description,
            "original_code": self.original_code,
            "refactored_code": self.refactored_code,
            "metadata": self.metadata,
        }


# ─── Policy / configuration types ─────────────────────────────────────────────


@dataclass
class PolicyInfo:
    """Metadata about a security policy.

    Attributes:
        name: Policy name (e.g., "default-secure").
        version: Policy version (e.g., "1.0").
        description: Human-readable policy description.
        blocked_patterns_count: Number of blocked file patterns.
        sensitive_patterns_count: Number of sensitive content patterns.
    """

    name: str
    version: str
    description: str
    blocked_patterns_count: int = 0
    sensitive_patterns_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy info to a dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "blocked_patterns_count": self.blocked_patterns_count,
            "sensitive_patterns_count": self.sensitive_patterns_count,
        }
