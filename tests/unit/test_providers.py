"""Unit tests for AI providers."""

import pytest
from ai_governance.providers import ProviderFactory, ClaudeProvider, OpenAIProvider
from ai_governance.core.exceptions import ConfigError, ProviderAuthError


def test_factory_creates_claude(provider_factory):
    """Test factory creates Claude provider with valid API key."""
    provider = provider_factory.create("claude", api_key="test-key-123")
    assert isinstance(provider, ClaudeProvider)
    assert provider.api_key == "test-key-123"


def test_factory_creates_openai(provider_factory):
    """Test factory creates OpenAI provider with valid API key."""
    provider = provider_factory.create("openai", api_key="test-key-456")
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "test-key-456"


def test_factory_unknown_provider(provider_factory):
    """Test factory raises error for unknown provider."""
    with pytest.raises(ConfigError, match="Unknown provider: unknown"):
        provider_factory.create("unknown", api_key="test-key")


def test_factory_lists_providers(provider_factory):
    """Test factory lists available providers."""
    providers = provider_factory.get_available_providers()
    assert "claude" in providers
    assert "openai" in providers
    assert len(providers) >= 2


def test_factory_checks_provider_availability(provider_factory):
    """Test factory checks if provider is available."""
    assert provider_factory.is_provider_available("claude") is True
    assert provider_factory.is_provider_available("openai") is True
    assert provider_factory.is_provider_available("unknown") is False


def test_factory_get_provider_info(provider_factory):
    """Test factory returns provider info."""
    info = provider_factory.get_provider_info("claude")
    assert info["name"] == "claude"
    assert info["class"] == "ClaudeProvider"
    assert "Claude" in info["doc"]


def test_factory_get_all_providers_info(provider_factory):
    """Test factory returns all providers info."""
    all_info = provider_factory.get_all_providers_info()
    assert "claude" in all_info
    assert "openai" in all_info
    assert all_info["claude"]["class"] == "ClaudeProvider"
    assert all_info["openai"]["class"] == "OpenAIProvider"


def test_claude_provider_requires_api_key():
    """Test Claude provider requires API key."""
    with pytest.raises(ProviderAuthError, match="API key"):
        ClaudeProvider(api_key=None)


def test_claude_provider_accepts_custom_model():
    """Test Claude provider accepts custom model."""
    provider = ClaudeProvider(api_key="test-key", model="custom-model")
    assert provider.model == "custom-model"


def test_claude_provider_uses_default_model():
    """Test Claude provider uses default model when not specified."""
    provider = ClaudeProvider(api_key="test-key")
    assert provider.model == ClaudeProvider.DEFAULT_MODEL


def test_claude_provider_model_info():
    """Test Claude provider returns model info."""
    provider = ClaudeProvider(api_key="test-key")
    info = provider.get_model_info()

    assert info["provider"] == "claude"
    assert "model" in info
    assert "input_price_per_1m" in info
    assert "output_price_per_1m" in info
    assert "max_tokens" in info
    assert isinstance(info["input_price_per_1m"], (int, float))
    assert isinstance(info["output_price_per_1m"], (int, float))


def test_openai_provider_requires_api_key():
    """Test OpenAI provider requires API key."""
    with pytest.raises(ProviderAuthError, match="API key"):
        OpenAIProvider(api_key=None)


def test_openai_provider_accepts_custom_model():
    """Test OpenAI provider accepts custom model."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4-turbo")
    assert provider.model == "gpt-4-turbo"


def test_openai_provider_model_info():
    """Test OpenAI provider returns model info."""
    provider = OpenAIProvider(api_key="test-key")
    info = provider.get_model_info()

    assert info["provider"] == "openai"
    assert "model" in info
    assert "input_price_per_1m" in info
    assert "output_price_per_1m" in info
