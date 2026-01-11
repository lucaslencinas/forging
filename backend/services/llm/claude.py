"""
Anthropic Claude LLM provider.
"""
import os
import logging
from typing import Optional

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API provider."""

    MODELS = [
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
    ]

    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.enabled = os.getenv("CLAUDE_ENABLED", "true").lower() == "true"
        self.model = model or self.MODELS[0]
        self._client = None

    @property
    def name(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        return bool(self.api_key) and self.enabled

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.name,
                error="ANTHROPIC_API_KEY not configured"
            )

        client = self._get_client()

        models_to_try = [self.model] if self.model not in self.MODELS else self.MODELS
        last_error = None

        for model_name in models_to_try:
            try:
                message = client.messages.create(
                    model=model_name,
                    max_tokens=2048,
                    system=system_prompt or "",
                    messages=[{"role": "user", "content": prompt}]
                )
                return LLMResponse(
                    content=message.content[0].text,
                    model=model_name,
                    provider=self.name
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Claude model {model_name} failed: {e}")
                continue

        return LLMResponse(
            content="",
            model=self.model,
            provider=self.name,
            error=f"All Claude models failed. Last error: {last_error}"
        )
