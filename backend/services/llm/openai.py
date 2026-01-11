"""
OpenAI LLM provider.
"""

import os
import logging
from typing import Optional

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    MODELS = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
    ]

    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = os.getenv("OPENAI_ENABLED", "true").lower() == "true"
        self.model = model or self.MODELS[0]
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return bool(self.api_key) and self.enabled

    def _get_client(self):
        if self._client is None:
            import openai

            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.name,
                error="OPENAI_API_KEY not configured",
            )

        client = self._get_client()

        models_to_try = [self.model] if self.model not in self.MODELS else self.MODELS
        last_error = None

        for model_name in models_to_try:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = client.chat.completions.create(
                    model=model_name, messages=messages, max_tokens=2048
                )
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=model_name,
                    provider=self.name,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"OpenAI model {model_name} failed: {e}")
                continue

        return LLMResponse(
            content="",
            model=self.model,
            provider=self.name,
            error=f"All OpenAI models failed. Last error: {last_error}",
        )
