"""
Base pipeline class for game-specific analysis.

All game pipelines inherit from BasePipeline and implement:
- analyze(): Run the full analysis pipeline
- get_game_type(): Return the game type identifier
- to_api_response(): Convert output to API response format
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelineOutput(BaseModel):
    """Output from any game pipeline - converted to API response."""

    tips: list[Any] = Field(default_factory=list, description="Game-specific tip type")
    summary_text: str = Field(default="", description="100-300 char summary for TTS")
    metadata: dict = Field(default_factory=dict, description="Pipeline execution stats")


class BasePipeline(ABC):
    """
    Base class for game-specific analysis pipelines.

    Each game (CS2, AoE2, etc.) implements its own pipeline that:
    1. Orchestrates game-specific Observer and Validator agents
    2. Handles game-specific data formats and analysis strategies
    3. Converts output to the unified API response format
    """

    def __init__(
        self,
        video_file: Any,
        replay_data: Optional[dict] = None,
    ):
        """
        Initialize a game pipeline.

        Args:
            video_file: Gemini file object (already uploaded)
            replay_data: Parsed replay/demo data
        """
        self.video_file = video_file
        self.replay_data = replay_data or {}

    @abstractmethod
    async def analyze(self) -> PipelineOutput:
        """
        Run the full analysis pipeline.

        Returns:
            PipelineOutput with tips, summary, and metadata
        """
        pass

    @abstractmethod
    def get_game_type(self) -> str:
        """
        Return the game type identifier.

        Returns:
            Game type string: 'cs2', 'aoe2', etc.
        """
        pass

    @abstractmethod
    def to_api_response(self, output: PipelineOutput) -> dict:
        """
        Convert pipeline output to API response format.

        Args:
            output: PipelineOutput from analyze()

        Returns:
            Dict that can be used to construct VideoAnalysisResponse
        """
        pass
