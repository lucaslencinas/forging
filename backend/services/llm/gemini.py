"""
Google Gemini LLM provider.
"""
import os
import logging
from typing import Optional

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Gemini API provider."""

    # Models to try in order of preference (all available on free AI Studio tier)
    MODELS = [
        "gemini-2.0-flash",      # Free tier, multimodal (text, image, video, audio)
        "gemini-1.5-flash",      # Free tier fallback, stable and widely available
        "gemini-1.5-pro",        # Free tier fallback, higher quality
    ]

    def __init__(self, model: Optional[str] = None):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.enabled = os.getenv("GEMINI_ENABLED", "true").lower() == "true"
        self.model = model or self.MODELS[0]
        self._genai = None

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key) and self.enabled

    def _get_client(self):
        if self._genai is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
        return self._genai

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.name,
                error="GEMINI_API_KEY not configured"
            )

        genai = self._get_client()

        # Try models in order until one works
        models_to_try = [self.model] if self.model not in self.MODELS else self.MODELS
        last_error = None

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt
                )
                response = model.generate_content(prompt)
                return LLMResponse(
                    content=response.text,
                    model=model_name,
                    provider=self.name
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Gemini model {model_name} failed: {e}")
                continue

        return LLMResponse(
            content="",
            model=self.model,
            provider=self.name,
            error=f"All Gemini models failed. Last error: {last_error}"
        )
