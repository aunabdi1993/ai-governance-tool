"""Factory for creating AI provider instances.

The ProviderFactory uses the Factory pattern to create and manage AI provider
instances. This decouples provider instantiation from client code and provides
a centralized place to configure providers.

Example:
    >>> from ai_governance.providers import ProviderFactory
    >>> factory = ProviderFactory()
    >>> provider = factory.create("claude", api_key="sk-...")
    >>> result = provider.refactor_code(code="def foo(): pass", ...)

    Or with default configuration:
    >>> factory = ProviderFactory()
    >>> provider = factory.create("claude")  # Uses ANTHROPIC_API_KEY env var
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type

from ..core.base import AIProvider
from ..core.exceptions import ConfigError
from .claude import ClaudeProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for creating AI provider instances.

    The ProviderFactory uses the Factory pattern to create provider instances
    and manage provider registration. It enables loose coupling between the tool's
    core logic and specific provider implementations.

    Providers can be easily extended by registering new provider classes.

    Attributes:
        _providers: Dictionary mapping provider names to provider classes.

    Example:
        >>> factory = ProviderFactory()
        >>> provider = factory.create("claude", api_key="sk-...")
        >>> print(provider.get_model_info())
        {
            "provider": "claude",
            "model": "claude-sonnet-4-5-20250929",
            ...
        }

        Or register a custom provider:
        >>> class CustomProvider(AIProvider):
        ...     pass
        >>> factory.register("custom", CustomProvider)
        >>> provider = factory.create("custom", api_key="...")
    """

    def __init__(self) -> None:
        """Initialize the provider factory with built-in providers."""
        self._providers: Dict[str, Type[AIProvider]] = {}
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        """Register the built-in provider implementations."""
        self.register("claude", ClaudeProvider)
        self.register("openai", OpenAIProvider)
        logger.debug("Registered built-in providers: claude, openai")

    def register(self, name: str, provider_class: Type[AIProvider]) -> None:
        """Register a provider implementation.

        Args:
            name: Name to associate with the provider (e.g., "claude", "openai").
            provider_class: Provider class (must implement AIProvider).

        Raises:
            TypeError: If provider_class does not implement AIProvider.

        Example:
            >>> class MyCustomProvider(AIProvider):
            ...     pass
            >>> factory = ProviderFactory()
            >>> factory.register("custom", MyCustomProvider)
        """
        if not issubclass(provider_class, AIProvider):
            raise TypeError(
                f"Provider class must implement AIProvider, got {provider_class.__name__}"
            )

        self._providers[name] = provider_class
        logger.debug(f"Registered provider: {name} -> {provider_class.__name__}")

    def create(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> AIProvider:
        """Create a provider instance.

        Args:
            provider_name: Name of the provider to create (e.g., "claude", "openai").
            api_key: API key for the provider. If not provided, uses environment variable.
            model: Model to use. If not provided, uses provider default.
            **kwargs: Additional arguments passed to the provider constructor.

        Returns:
            Provider instance ready to use.

        Raises:
            ConfigError: If the provider is not registered.

        Example:
            >>> factory = ProviderFactory()
            >>> provider = factory.create("claude", api_key="sk-...")
            >>> provider = factory.create(
            ...     "openai",
            ...     api_key="sk-...",
            ...     model="gpt-4-turbo"
            ... )
        """
        if provider_name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ConfigError(
                f"Unknown provider: {provider_name}. Available providers: {available}",
                details={"provider": provider_name, "available": list(self._providers.keys())},
            )

        provider_class = self._providers[provider_name]

        logger.debug(
            f"Creating {provider_name} provider instance with model={model or 'default'}"
        )

        try:
            return provider_class(api_key=api_key, model=model, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {e}")
            raise

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names.

        Returns:
            List of registered provider names.

        Example:
            >>> factory = ProviderFactory()
            >>> providers = factory.get_available_providers()
            >>> print(providers)
            ['claude', 'openai']
        """
        return list(self._providers.keys())

    def is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is registered.

        Args:
            provider_name: Name of the provider to check.

        Returns:
            True if the provider is registered, False otherwise.

        Example:
            >>> factory = ProviderFactory()
            >>> factory.is_provider_available("claude")
            True
            >>> factory.is_provider_available("unknown")
            False
        """
        return provider_name in self._providers

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a registered provider.

        Args:
            provider_name: Name of the provider.

        Returns:
            Dictionary with provider information.

        Raises:
            ConfigError: If the provider is not registered.

        Example:
            >>> factory = ProviderFactory()
            >>> info = factory.get_provider_info("claude")
            >>> print(info)
            {
                "name": "claude",
                "class": "ClaudeProvider",
                "module": "ai_governance.providers.claude",
            }
        """
        if not self.is_provider_available(provider_name):
            raise ConfigError(
                f"Provider not found: {provider_name}",
                details={"provider": provider_name},
            )

        provider_class = self._providers[provider_name]

        return {
            "name": provider_name,
            "class": provider_class.__name__,
            "module": provider_class.__module__,
            "doc": provider_class.__doc__,
        }

    def get_all_providers_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered providers.

        Returns:
            Dictionary mapping provider names to their information.

        Example:
            >>> factory = ProviderFactory()
            >>> info = factory.get_all_providers_info()
            >>> for name, details in info.items():
            ...     print(f"{name}: {details['class']}")
        """
        return {name: self.get_provider_info(name) for name in self.get_available_providers()}
