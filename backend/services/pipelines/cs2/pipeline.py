"""
CS2 Pipeline - Round-Based Video Analysis.

Orchestrates the CS2-specific analysis flow:
1. Round Detector: Quick LLM call to detect which rounds are in the video
2. Observer: Single-pass multi-angle analysis (10-20 tips)
3. Validator: 2-step verification with confidence scoring
"""

import logging
import time
from typing import Any, Optional

from services.agents.base import get_gemini_client
from services.pipelines.base import BasePipeline, PipelineOutput
from services.pipelines.cs2.contracts import CS2PipelineOutput, RoundTimeline
from services.pipelines.cs2.observer import CS2ObserverAgent
from services.pipelines.cs2.round_detector import (
    build_rounds_timeline_from_demo,
    detect_video_rounds,
    filter_demo_data_by_rounds,
)
from services.pipelines.cs2.validator import CS2ValidatorAgent

logger = logging.getLogger(__name__)


class CS2Pipeline(BasePipeline):
    """
    CS2-specific analysis pipeline.

    Flow:
    1. Round Detector: Quick LLM call to detect which rounds are in the video
    2. Observer: Multi-angle analysis (generates 10-20 tips)
    3. Validator: Cross-check and confidence scoring

    Key features:
    - Round detection to filter demo data
    - Death timeline awareness (skip spectating footage)
    - Round-based video navigation support
    """

    def __init__(
        self,
        video_file: Any,
        replay_data: Optional[dict] = None,
    ):
        """Initialize CS2 pipeline."""
        super().__init__(video_file, replay_data)
        self.client = get_gemini_client()

    def get_game_type(self) -> str:
        """Return CS2 game type."""
        return "cs2"

    async def analyze(self) -> PipelineOutput:
        """
        Run the full CS2 analysis pipeline.

        Returns:
            PipelineOutput with tips, summary, and metadata
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("CS2 PIPELINE STARTING")
        logger.info("=" * 60)
        logger.info(f"    Video: {self.video_file.name}")

        # ======================================================================
        # Step 0: Round Detection
        # ======================================================================
        filtered_replay_data = self.replay_data
        round_detection_time = 0

        logger.info("\n" + "=" * 60)
        logger.info("[0/3] ROUND DETECTOR - Detecting rounds in video")
        logger.info("=" * 60)
        step_start = time.time()

        round_info = await detect_video_rounds(
            self.client,
            self.video_file,
        )

        round_detection_time = time.time() - step_start
        logger.info(f"[round_detector] Complete in {round_detection_time:.1f}s")

        if round_info.get("detected"):
            first_round = round_info.get("first_round")
            last_round = round_info.get("last_round")
            logger.info(f"[round_detector] Video covers rounds {first_round} - {last_round}")

            # Filter the demo data
            filtered_replay_data = filter_demo_data_by_rounds(
                self.replay_data,
                first_round,
                last_round,
            )
        else:
            logger.warning("[round_detector] Could not detect rounds, using full demo data")

        # ======================================================================
        # Build authoritative rounds timeline from demo data
        # ======================================================================
        # This is deterministic and uses demo tick data, not LLM detection
        demo_rounds_timeline = []
        if filtered_replay_data and filtered_replay_data.get("rounds"):
            demo_rounds_timeline = build_rounds_timeline_from_demo(
                filtered_replay_data,
                pov_player=filtered_replay_data.get("pov_player"),
            )
            logger.info(
                f"[pipeline] Using DEMO-BASED rounds timeline: {len(demo_rounds_timeline)} rounds "
                f"(rounds {demo_rounds_timeline[0]['round']}-{demo_rounds_timeline[-1]['round']})"
            )
        else:
            logger.warning(
                "[pipeline] No demo data available - rounds timeline will come from LLM (less reliable)"
            )
        # Store in filtered_replay_data for agents to use
        filtered_replay_data["rounds_timeline_demo"] = demo_rounds_timeline

        # ======================================================================
        # Step 1: Observer - Multi-angle analysis
        # ======================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[1/2] OBSERVER - Multi-Angle Analysis")
        logger.info("    Perspectives: Exploitable Patterns, Rank-Up Habits, Missed Adaptations")
        logger.info("=" * 60)
        step_start = time.time()

        observer = CS2ObserverAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=filtered_replay_data,
            game_type="cs2",
        )

        observer_output, _ = await observer.process({})

        observer_time = time.time() - step_start
        logger.info(f"[observer] Complete in {observer_time:.1f}s")
        logger.info(f"[observer] -> {len(observer_output.tips)} tips generated")

        # ======================================================================
        # Step 2: Validator - Cross-check and confidence scoring
        # ======================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[2/2] VALIDATOR - Cross-Check & Confidence Scoring")
        logger.info("    Step 1: Video cross-check (5s before/after each timestamp)")
        logger.info("    Step 2: Verify POV player actions")
        logger.info("    Keeping tips with confidence >= 8")
        logger.info("=" * 60)
        step_start = time.time()

        validator = CS2ValidatorAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=filtered_replay_data,
        )

        final_output = await validator.verify(observer_output)

        validator_time = time.time() - step_start
        logger.info(f"[validator] Complete in {validator_time:.1f}s")
        logger.info(f"[validator] -> {len(final_output.tips)} tips verified")

        # ======================================================================
        # Pipeline Complete
        # ======================================================================
        total_time = time.time() - start_time

        # Build metadata
        final_output.pipeline_metadata.update({
            "total_time_seconds": round(total_time, 1),
            "round_detection_time_seconds": round(round_detection_time, 1),
            "observer_time_seconds": round(observer_time, 1),
            "validator_time_seconds": round(validator_time, 1),
            "observer_tips_count": len(observer_output.tips),
            "final_tips_count": len(final_output.tips),
            "video_rounds": filtered_replay_data.get("video_rounds"),
        })

        logger.info("\n" + "=" * 60)
        logger.info("CS2 PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"    Total time: {total_time:.1f}s")
        logger.info(f"    Round detection: {round_detection_time:.1f}s")
        logger.info(f"    Observer: {len(observer_output.tips)} tips in {observer_time:.1f}s")
        logger.info(f"    Validator: {len(final_output.tips)} tips verified in {validator_time:.1f}s")
        logger.info(f"    Final tips: {len(final_output.tips)}")
        logger.info("=" * 60)

        # Convert to generic PipelineOutput
        # Use demo-built timeline (deterministic) instead of LLM-detected timeline
        return PipelineOutput(
            tips=final_output.tips,
            summary_text=final_output.summary_text,
            metadata={
                **final_output.pipeline_metadata,
                "rounds_timeline": demo_rounds_timeline,  # Demo-based, not LLM-based
                "observer_output": observer_output.model_dump(),
            },
        )

    def to_api_response(self, output: PipelineOutput) -> dict:
        """
        Convert CS2 pipeline output to API response format.

        Args:
            output: PipelineOutput from analyze()

        Returns:
            Dict with API response fields
        """
        # Extract rounds_timeline from metadata
        rounds_timeline_raw = output.metadata.get("rounds_timeline", [])
        rounds_timeline = [RoundTimeline(**r) for r in rounds_timeline_raw]

        return {
            "game_type": "cs2",
            "tips": output.tips,
            "summary_text": output.summary_text,
            "rounds_timeline": rounds_timeline,
            "model_used": "gemini-3-pro-preview",
            "provider": "gemini",
            "pipeline_metadata": output.metadata,
        }
