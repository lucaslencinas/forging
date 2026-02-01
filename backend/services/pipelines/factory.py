"""
Pipeline factory for creating game-specific pipelines.
"""

from typing import Any, Optional

from .base import BasePipeline


class PipelineFactory:
    """
    Factory for creating game-specific analysis pipelines.

    Usage:
        pipeline = PipelineFactory.create("cs2", video_file, replay_data)
        output = await pipeline.analyze()
    """

    @staticmethod
    def create(
        game_type: str,
        video_file: Any,
        replay_data: Optional[dict] = None,
    ) -> BasePipeline:
        """
        Create a pipeline for the specified game type.

        Args:
            game_type: Game identifier ('cs2', 'aoe2')
            video_file: Gemini file object (already uploaded)
            replay_data: Parsed replay/demo data

        Returns:
            Game-specific pipeline instance

        Raises:
            ValueError: If game_type is not supported
        """
        if game_type == "cs2":
            from .cs2.pipeline import CS2Pipeline

            return CS2Pipeline(video_file, replay_data)

        elif game_type == "aoe2":
            from .aoe2.pipeline import AoE2Pipeline

            return AoE2Pipeline(video_file, replay_data)

        else:
            raise ValueError(f"Unsupported game type: {game_type}")
