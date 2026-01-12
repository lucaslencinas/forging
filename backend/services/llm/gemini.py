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
    """Gemini API provider."""

    # Models to try in order of preference (all available on free AI Studio tier)
    MODELS = [
        "gemini-2.0-flash",      # Free tier, multimodal (text, image, video, audio)
        "gemini-1.5-flash",      # Free tier fallback, stable and widely available
        "gemini-1.5-pro",        # Free tier fallback, higher quality
    ]

    # Video analysis models (configurable via env or UI)
    VIDEO_MODELS = [
        "gemini-2.5-flash",      # Best price/performance, thinking model
        "gemini-2.5-pro",        # Best quality, reasoning
        "gemini-3-flash-preview",    # Newest flash model (experimental)
        "gemini-3-pro-preview",      # Newest pro model (experimental)
        "gemini-2.0-flash",      # Stable, fast
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
        model: Optional[str] = None
    ) -> VideoAnalysisResult:
        """
        Analyze a video using Gemini's multimodal capabilities.

        Args:
            file_name: The Gemini file name from upload_video()
            prompt: The analysis prompt
            system_prompt: Optional system instructions
            model: Optional model override (defaults to gemini-2.0-flash)

        Returns:
            VideoAnalysisResult with the analysis content
        """
        if not self.is_available():
            return VideoAnalysisResult(
                content="",
                model=self.model,
                provider=self.name,
                file_name=file_name,
                error="GEMINI_API_KEY not configured"
            )

        genai = self._get_client()
        model_name = model or os.getenv("VIDEO_ANALYSIS_MODEL", "gemini-2.5-flash")

        try:
            # Get the file reference
            video_file = genai.get_file(file_name)

            # Create model with system prompt and low temperature for accuracy
            generation_config = genai.GenerationConfig(
                temperature=0.2,  # Low temperature for factual, less creative responses
            )
            gemini_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                generation_config=generation_config
            )

            # Generate content with video + text prompt
            # Set longer timeout for video analysis (default is 60s, videos can take 2-5 min)
            logger.info(f"Analyzing video with model: {model_name}")
            request_options = {"timeout": 600}  # 10 minute timeout
            response = gemini_model.generate_content(
                [video_file, prompt],
                request_options=request_options
            )

            return VideoAnalysisResult(
                content=response.text,
                model=model_name,
                provider=self.name,
                file_name=file_name
            )
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return VideoAnalysisResult(
                content="",
                model=model_name,
                provider=self.name,
                file_name=file_name,
                error=str(e)
            )
