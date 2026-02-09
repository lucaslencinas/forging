"""
AoE2 Pipeline - Phase-Based Video Analysis.

Orchestrates the AoE2-specific analysis flow:
1. Observer: Single-pass multi-angle analysis (10-20 tips)
2. Validator: 2-step verification with confidence scoring

Key differences from CS2:
- No round detection (continuous gameplay)
- Game time vs video time conversion (1.5x speed)
- Phase-based analysis (Dark/Feudal/Castle/Imperial)
"""

import logging
import time
from typing import Any, Optional

from services.agents.base import get_gemini_client
from services.pipelines.base import BasePipeline, PipelineOutput
from services.pipelines.aoe2.contracts import AoE2PipelineOutput
from services.pipelines.aoe2.observer import AoE2ObserverAgent
from services.pipelines.aoe2.validator import AoE2ValidatorAgent

logger = logging.getLogger(__name__)


class AoE2Pipeline(BasePipeline):
    """
    AoE2-specific analysis pipeline.

    Flow:
    1. Observer: Multi-angle analysis (generates 10-20 tips)
    2. Validator: Cross-check and confidence scoring

    Key features:
    - Handles game time vs video time conversion (1.5x)
    - Uses replay data for ground truth verification
    - Phase-aware analysis (Dark/Feudal/Castle/Imperial)
    """

    def __init__(
        self,
        video_file: Any,
        replay_data: Optional[dict] = None,
    ):
        """Initialize AoE2 pipeline."""
        super().__init__(video_file, replay_data)
        self.client = get_gemini_client()

    def get_game_type(self) -> str:
        """Return AoE2 game type."""
        return "aoe2"

    async def analyze(self) -> PipelineOutput:
        """
        Run the full AoE2 analysis pipeline.

        Returns:
            PipelineOutput with tips, summary, and metadata
        """
        start_time = time.time()

        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info("[GAME-ANALYSIS] AOE2 PIPELINE STARTING")
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info(f"[GAME-ANALYSIS] Video: {self.video_file.name}")

        # ======================================================================
        # Step 1: Observer - Multi-angle analysis
        # ======================================================================
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info("[GAME-ANALYSIS] [1/2] OBSERVER - Multi-Angle Analysis")
        logger.info("[GAME-ANALYSIS] Perspectives: Exploitable Patterns, Rank-Up Habits, Missed Adaptations")
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        step_start = time.time()

        observer = AoE2ObserverAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=self.replay_data,
            game_type="aoe2",
        )

        observer_output, observer_interaction_id = await observer.process({})

        observer_time = time.time() - step_start
        logger.info(f"[GAME-ANALYSIS] [observer] Complete in {observer_time:.1f}s")
        logger.info(f"[GAME-ANALYSIS] [observer] -> {len(observer_output.tips)} tips generated")

        # ======================================================================
        # Step 2: Validator - Cross-check and confidence scoring
        # ======================================================================
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info("[GAME-ANALYSIS] [2/2] VALIDATOR - Cross-Check & Confidence Scoring")
        logger.info("[GAME-ANALYSIS] Keeping tips with confidence >= 8")
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        step_start = time.time()

        validator = AoE2ValidatorAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=self.replay_data,
        )

        final_output = await validator.verify(
            observer_output,
            previous_interaction_id=observer_interaction_id,
        )

        validator_time = time.time() - step_start
        logger.info(f"[GAME-ANALYSIS] [validator] Complete in {validator_time:.1f}s")
        logger.info(f"[GAME-ANALYSIS] [validator] -> {len(final_output.tips)} tips verified")

        # ======================================================================
        # Pipeline Complete
        # ======================================================================
        total_time = time.time() - start_time

        # Build metadata
        final_output.pipeline_metadata.update({
            "total_time_seconds": round(total_time, 1),
            "observer_time_seconds": round(observer_time, 1),
            "validator_time_seconds": round(validator_time, 1),
            "observer_tips_count": len(observer_output.tips),
            "final_tips_count": len(final_output.tips),
        })

        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info("[GAME-ANALYSIS] AOE2 PIPELINE COMPLETE")
        logger.info("[GAME-ANALYSIS] " + "=" * 50)
        logger.info(f"[GAME-ANALYSIS] Total time: {total_time:.1f}s")
        logger.info(f"[GAME-ANALYSIS] Observer: {len(observer_output.tips)} tips in {observer_time:.1f}s")
        logger.info(f"[GAME-ANALYSIS] Validator: {len(final_output.tips)} tips verified in {validator_time:.1f}s")
        logger.info(f"[GAME-ANALYSIS] Final tips: {len(final_output.tips)}")
        logger.info("[GAME-ANALYSIS] " + "=" * 50)

        # Convert to generic PipelineOutput
        return PipelineOutput(
            tips=final_output.tips,
            summary_text=final_output.summary_text,
            metadata={
                **final_output.pipeline_metadata,
                "observer_output": observer_output.model_dump(),
            },
            last_interaction_id=final_output.last_interaction_id,
        )

    def to_api_response(self, output: PipelineOutput) -> dict:
        """
        Convert AoE2 pipeline output to API response format.

        Args:
            output: PipelineOutput from analyze()

        Returns:
            Dict with API response fields
        """
        return {
            "game_type": "aoe2",
            "tips": output.tips,
            "summary_text": output.summary_text,
            "model_used": "gemini-3-pro-preview",
            "provider": "gemini",
            "pipeline_metadata": output.metadata,
        }
