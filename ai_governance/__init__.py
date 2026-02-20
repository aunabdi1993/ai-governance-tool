"""
AI Governance Tool - Enterprise-grade AI-assisted code refactoring with policy controls.

A production-ready tool for secure, policy-driven code refactoring using multiple AI providers
(Claude, OpenAI, etc.) with comprehensive audit logging, security scanning, and governance controls.
"""

__version__ = "1.0.0"

# Import core components for easy access
from ai_governance.core.exceptions import (
    AIGovernanceError,
    PolicyViolationError,
    SecurityViolationError,
    ProviderError,
    ConfigError,
)

__all__ = [
    "__version__",
    "AIGovernanceError",
    "PolicyViolationError",
    "SecurityViolationError",
    "ProviderError",
    "ConfigError",
]
