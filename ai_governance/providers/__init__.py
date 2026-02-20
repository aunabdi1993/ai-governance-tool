"""AI provider implementations for AI Governance Tool.

This package contains concrete implementations of the AIProvider abstract base class,
enabling the tool to work with different AI APIs (Claude, OpenAI, etc.).

Providers:
    - claude: Anthropic Claude API implementation
    - openai_provider: OpenAI GPT API implementation
    - factory: ProviderFactory for creating provider instances

Example:
    >>> from ai_governance.providers import ClaudeProvider
    >>> provider = ClaudeProvider(api_key="sk-...")
    >>> result = provider.refactor_code(code="def foo(): pass", target="add type hints", filepath="main.py")
    >>> print(result.success)
    True

    Or using the factory pattern:
    >>> from ai_governance.providers import ProviderFactory
    >>> factory = ProviderFactory()
    >>> provider = factory.create("claude", api_key="sk-...")
    >>> result = provider.refactor_code(...)
"""

from __future__ import annotations

from .claude import ClaudeProvider
from .factory import ProviderFactory
from .openai_provider import OpenAIProvider

__all__ = [
    "ClaudeProvider",
    "OpenAIProvider",
    "ProviderFactory",
]
