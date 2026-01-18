"""
LLM provider factory with fallback support.
"""
import logging
from typing import Optional

from .base import LLMProvider, LLMResponse
from .gemini import GeminiProvider
from .claude import ClaudeProvider
from .openai import OpenAIProvider

logger = logging.getLogger(__name__)

# Provider registry
PROVIDERS = {
    "gemini": GeminiProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}

# Default order for fallback
# Gemini is primary, OpenAI is fallback for rate limits/errors
DEFAULT_PROVIDER_ORDER = ["gemini", "openai"]


def get_available_providers() -> list[str]:
    """Return list of configured/available provider names."""
    available = []
    for name, cls in PROVIDERS.items():
        provider = cls()
        if provider.is_available():
            available.append(name)
    return available


def get_llm_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None
) -> LLMProvider:
    """
    Get an LLM provider instance.

    Args:
        provider_name: Specific provider to use. If None, uses first available.
        model: Specific model to use. If None, uses provider default.

    Returns:
        LLMProvider instance
    """
    if provider_name:
        if provider_name not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDERS.keys())}")
        return PROVIDERS[provider_name](model=model)

    # Find first available provider
    for name in DEFAULT_PROVIDER_ORDER:
        provider = PROVIDERS[name](model=model)
        if provider.is_available():
            logger.info(f"Using LLM provider: {name}")
            return provider

    # Return a provider that will report the error
    return GeminiProvider(model=model)


class FallbackProvider(LLMProvider):
    """Provider that tries multiple providers in order until one succeeds."""

    def __init__(self, providers: Optional[list[str]] = None):
        self.provider_names = providers or DEFAULT_PROVIDER_ORDER
        self._providers = [
            PROVIDERS[name]() for name in self.provider_names
            if name in PROVIDERS
        ]

    @property
    def name(self) -> str:
        return "fallback"

    def is_available(self) -> bool:
        return any(p.is_available() for p in self._providers)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        for provider in self._providers:
            if not provider.is_available():
                continue

            response = await provider.generate(prompt, system_prompt)
            if response.success:
                return response
            logger.warning(f"Provider {provider.name} failed: {response.error}")

        return LLMResponse(
            content="",
            model="none",
            provider="fallback",
            error="All providers failed or unavailable"
        )
