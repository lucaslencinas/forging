"""
Google Gemini LLM provider with File API support for video analysis.
"""

import os
import logging
import time
from typing import Optional
from dataclasses import dataclass

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class VideoAnalysisResult:
    """Result from video analysis."""

    content: str
    model: str
    provider: str
    file_name: str  # Gemini file reference for cleanup
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class GeminiProvider(LLMProvider):
    """Gemini API provider with multi-key support and rate limit fallback."""

    # Default models (can be overridden via GEMINI_MODEL and GEMINI_FAST_MODEL env vars)
    # Primary model for quality tasks (analysis, validation, chat)
    DEFAULT_MODEL = "gemini-3-pro-preview"
    # Fast model for quick tasks (round detection, simple parsing)
    DEFAULT_FAST_MODEL = "gemini-3-flash-preview"

    # Fallback models if primary fails (in order of preference)
    FALLBACK_MODELS = [
        "gemini-3-flash-preview",  # Fast Gemini 3
        "gemini-2.5-pro",  # Best quality Gemini 2.5
        "gemini-2.5-flash",  # Fast Gemini 2.5
        "gemini-2.0-flash",  # Stable fallback
    ]

    # Cooldown period for rate-limited keys (24 hours for daily quota limits)
    KEY_COOLDOWN_SECONDS = 86400

    def __init__(self, model: Optional[str] = None):
        # Support multiple API keys with fallback
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        if api_keys_str:
            self.api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        else:
            # Fallback to single key for backwards compatibility
            single_key = os.getenv("GEMINI_API_KEY", "")
            self.api_keys = [single_key] if single_key else []

        self._current_key_index = 0
        self._key_cooldowns: dict[int, float] = {}  # index -> cooldown_until timestamp

        self.enabled = os.getenv("GEMINI_ENABLED", "true").lower() == "true"
        self.model = model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        self._genai = None
        self._configured_key: Optional[str] = None  # Track which key is configured

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self._get_current_api_key()) and self.enabled

    def _get_current_api_key(self) -> Optional[str]:
        """Get the current API key, skipping keys on cooldown."""
        if not self.api_keys:
            return None

        now = time.time()
        for i in range(len(self.api_keys)):
            idx = (self._current_key_index + i) % len(self.api_keys)
            cooldown_until = self._key_cooldowns.get(idx, 0)
            if now >= cooldown_until:
                self._current_key_index = idx
                return self.api_keys[idx]

        # All keys on cooldown
        logger.warning("All Gemini API keys are on cooldown")
        return None

    def _rotate_key_on_rate_limit(self) -> bool:
        """Put current key on cooldown and rotate to next. Returns True if a new key is available."""
        if len(self.api_keys) <= 1:
            return False

        old_index = self._current_key_index
        self._key_cooldowns[old_index] = time.time() + self.KEY_COOLDOWN_SECONDS
        logger.warning(
            f"API key #{old_index + 1} rate limited, putting on 24h cooldown"
        )

        # Try to find a non-cooldown key
        new_key = self._get_current_api_key()
        if new_key and self._current_key_index != old_index:
            logger.info(f"Rotated to API key #{self._current_key_index + 1}")
            # Reset client to use new key
            self._genai = None
            self._configured_key = None
            return True

        return False

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return (
            "429" in error_str
            or "rate limit" in error_str
            or "quota" in error_str
            or "resource exhausted" in error_str
        )

    def _get_client(self):
        current_key = self._get_current_api_key()
        if current_key is None:
            raise ValueError("No Gemini API key available (all keys on cooldown)")

        # Reconfigure if key changed
        if self._genai is None or self._configured_key != current_key:
            import google.generativeai as genai

            genai.configure(api_key=current_key)
            self._genai = genai
            self._configured_key = current_key
            if len(self.api_keys) > 1:
                logger.info(
                    f"Configured Gemini with API key #{self._current_key_index + 1} of {len(self.api_keys)}"
                )
        return self._genai

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> LLMResponse:
        if not self.is_available():
            return LLMResponse(
                content="",
                model=self.model,
                provider=self.name,
                error="GEMINI_API_KEY not configured or all keys on cooldown",
            )

        # Try with current key, rotate on rate limit
        max_key_attempts = len(self.api_keys)
        last_error = None

        for key_attempt in range(max_key_attempts):
            try:
                genai = self._get_client()

                # Try models in order until one works
                models_to_try = (
                    [self.model] if self.model not in self.MODELS else self.MODELS
                )

                for model_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(
                            model_name=model_name, system_instruction=system_prompt
                        )
                        response = model.generate_content(prompt)
                        return LLMResponse(
                            content=response.text, model=model_name, provider=self.name
                        )
                    except Exception as e:
                        last_error = e
                        logger.warning(f"Gemini model {model_name} failed: {e}")

                        # Check if rate limit error and try rotating key
                        if (
                            self._is_rate_limit_error(e)
                            and self._rotate_key_on_rate_limit()
                        ):
                            break  # Break inner loop to retry with new key
                        continue

                # If we get here without returning, all models failed for this key
                # Check if last error was rate limit and we should try another key
                if last_error and self._is_rate_limit_error(last_error):
                    if not self._rotate_key_on_rate_limit():
                        break  # No more keys available
                else:
                    break  # Not a rate limit error, don't retry

            except ValueError as e:
                # No API key available
                last_error = e
                break

        return LLMResponse(
            content="",
            model=self.model,
            provider=self.name,
            error=f"All Gemini API keys/models failed. Last error: {last_error}",
        )

    def upload_video(self, file_path: str, mime_type: str = "video/mp4") -> str:
        """
        Upload a video file to Gemini File API.

        Args:
            file_path: Path to the video file
            mime_type: MIME type of the video

        Returns:
            The file name/URI to reference in prompts

        Raises:
            Exception if upload or processing fails
        """
        genai = self._get_client()

        logger.info(f"Uploading video to Gemini: {file_path}")
        video_file = genai.upload_file(path=file_path, mime_type=mime_type)
        logger.info(f"Upload complete. File name: {video_file.name}")

        # Wait for file to be processed (ACTIVE state)
        max_wait_seconds = 300  # 5 minutes for large videos
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait_seconds:
            file_status = genai.get_file(video_file.name)
            state = file_status.state.name

            if state == "ACTIVE":
                logger.info(f"Video file ready: {video_file.name}")
                return video_file.name
            elif state == "FAILED":
                raise Exception(f"Video processing failed: {video_file.name}")

            logger.info(f"Video processing... state={state}, elapsed={elapsed}s")
            time.sleep(poll_interval)
            elapsed += poll_interval

        raise Exception(f"Video processing timed out after {max_wait_seconds}s")

    def delete_video(self, file_name: str) -> None:
        """Delete an uploaded video file from Gemini."""
        try:
            genai = self._get_client()
            genai.delete_file(file_name)
            logger.info(f"Deleted video file: {file_name}")
        except Exception as e:
            logger.warning(f"Failed to delete video file {file_name}: {e}")

    async def analyze_video(
        self,
        file_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        video_path: Optional[str] = None,
    ) -> VideoAnalysisResult:
        """
        Analyze a video using Gemini's multimodal capabilities.

        Args:
            file_name: The Gemini file name from upload_video()
            prompt: The analysis prompt
            system_prompt: Optional system instructions
            model: Optional model override (defaults to GEMINI_MODEL env var or gemini-3-pro-preview)
            video_path: Optional path to video file for re-upload on key rotation

        Returns:
            VideoAnalysisResult with the analysis content
        """
        current_file_name = file_name

        if not self.is_available():
            return VideoAnalysisResult(
                content="",
                model=self.model,
                provider=self.name,
                file_name=current_file_name,
                error="GEMINI_API_KEY not configured or all keys on cooldown",
            )

        model_name = model or os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        max_key_attempts = len(self.api_keys)
        last_error = None

        for key_attempt in range(max_key_attempts):
            try:
                genai = self._get_client()

                # Get the file reference
                video_file = genai.get_file(current_file_name)

                generation_config = genai.GenerationConfig()
                gemini_model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_prompt,
                    generation_config=generation_config,
                )

                # Generate content with video + text prompt
                # Set longer timeout for video analysis (default is 60s, videos can take 2-5 min)
                logger.info(f"Analyzing video with model: {model_name}")
                request_options = {"timeout": 600}  # 10 minute timeout
                response = gemini_model.generate_content(
                    [video_file, prompt], request_options=request_options
                )

                return VideoAnalysisResult(
                    content=response.text,
                    model=model_name,
                    provider=self.name,
                    file_name=current_file_name,
                )
            except Exception as e:
                last_error = e
                logger.error(f"Video analysis failed: {e}")

                # Check if rate limit error or file permission error
                is_rate_limit = self._is_rate_limit_error(e)
                is_file_permission = (
                    "do not have permission to access" in str(e).lower()
                    or "may not exist" in str(e).lower()
                )

                if (
                    is_rate_limit or is_file_permission
                ) and self._rotate_key_on_rate_limit():
                    # If we have video_path, re-upload with new key
                    if video_path:
                        logger.info("Re-uploading video with new API key...")
                        try:
                            new_file_name = self.upload_video(video_path)
                            if new_file_name:
                                current_file_name = new_file_name
                                logger.info(
                                    f"Video re-uploaded as: {current_file_name}"
                                )
                        except Exception as upload_error:
                            logger.error(f"Failed to re-upload video: {upload_error}")
                            break
                    logger.info("Retrying video analysis with new API key")
                    continue  # Retry with new key
                break  # Not a rate limit error or no more keys

        return VideoAnalysisResult(
            content="",
            model=model_name,
            provider=self.name,
            file_name=current_file_name,
            error=str(last_error) if last_error else "Unknown error",
        )
