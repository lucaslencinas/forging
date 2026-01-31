"""
Pipeline Orchestrator - 2-Agent Pipeline

Simplified architecture:
1. Round Detector: Quick LLM call to detect which rounds are in the video
2. Observer: Single-pass multi-angle analysis (10-20 tips)
3. Validator: 2-step verification with confidence scoring

Video + Replay Data
        |
        v
   +----------------+
   | Round Detector |  (quick call to detect rounds in video)
   +-------+--------+
           |
           v
   +----------+
   | Observer |  (single pass, multi-angle analysis)
   +----+-----+
        |
        v
   +-----------+
   | Validator |  (verify against video, remove hallucinations)
   +----+------+
        |
        v
   Final Output
"""

import json
import logging
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from .analyst import ObserverAgent
from .base import BaseAgent, get_gemini_client, upload_video_to_gemini
from .contracts import ProducerOutput
from .verifier import ValidatorAgent

logger = logging.getLogger(__name__)


async def detect_video_rounds(
    client: genai.Client,
    video_file: Any,
    game_type: str = "cs2",
) -> dict:
    """
    Quick LLM call to detect which rounds are shown in the video.

    Args:
        client: Gemini client
        video_file: Uploaded video file
        game_type: 'cs2' or 'aoe2'

    Returns:
        Dict with 'first_round' and 'last_round' keys
    """
    logger.info("[round_detector] Detecting rounds in video...")

    if game_type != "cs2":
        # For AoE2, we don't have rounds in the same way
        logger.info("[round_detector] Skipping for non-CS2 game")
        return {"first_round": None, "last_round": None, "detected": False}

    prompt = """Look at the CS2 gameplay video and identify the round numbers.

TASK:
1. Look at the FIRST 10 seconds of the video
2. Find the round counter in the HUD (usually shows like "Round 1" or "1" near the top)
3. Look at the LAST 10 seconds of the video
4. Find the round counter there too

The round number is typically shown:
- At the top center of the screen during gameplay
- On the scoreboard (press TAB view)
- During round start freeze time

Return ONLY this JSON (no other text):
{"first_round": X, "last_round": Y}

Where X is the first round number you see and Y is the last round number you see.
If you can't determine a round number, use null for that value.

Example responses:
{"first_round": 1, "last_round": 7}
{"first_round": 8, "last_round": 14}
{"first_round": 1, "last_round": null}
"""

    try:
        # Use a fast model for this quick detection
        model = os.getenv("TURTLE_FAST_MODEL", "gemini-2.0-flash")

        # Build content list with proper types for models.generate_content API
        input_content = [
            prompt,  # Text prompt as string
            types.Part(
                file_data=types.FileData(
                    file_uri=video_file.uri,
                    mime_type="video/mp4",
                )
            ),
        ]

        start_time = time.time()
        response = client.models.generate_content(
            model=model,
            contents=input_content,
        )

        elapsed = time.time() - start_time
        response_text = response.text if hasattr(response, "text") else str(response)

        logger.info(f"[round_detector] Response in {elapsed:.1f}s: {response_text[:200]}")

        # Extract JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
            first_round = result.get("first_round")
            last_round = result.get("last_round")

            logger.info(f"[round_detector] Detected rounds: {first_round} - {last_round}")

            return {
                "first_round": first_round,
                "last_round": last_round,
                "detected": first_round is not None or last_round is not None,
            }
        else:
            logger.warning(f"[round_detector] Could not parse JSON from response")
            return {"first_round": None, "last_round": None, "detected": False}

    except Exception as e:
        logger.error(f"[round_detector] Error detecting rounds: {e}")
        return {"first_round": None, "last_round": None, "detected": False, "error": str(e)}


def filter_demo_data_by_rounds(
    demo_data: dict,
    first_round: int,
    last_round: int,
) -> dict:
    """
    Filter demo data to only include data for the specified round range.

    Args:
        demo_data: Full parsed demo data
        first_round: First round number (inclusive)
        last_round: Last round number (inclusive)

    Returns:
        Filtered demo data with only the relevant rounds
    """
    if first_round is None and last_round is None:
        return demo_data

    # Default to round 1 if first_round not detected
    if first_round is None:
        first_round = 1

    # Default to a high number if last_round not detected
    if last_round is None:
        last_round = 999

    logger.info(f"[filter] Filtering demo data to rounds {first_round}-{last_round}")

    filtered = demo_data.copy()

    # Filter rounds
    rounds = demo_data.get("rounds", [])
    filtered_rounds = [r for r in rounds if first_round <= r.get("round_num", 0) <= last_round]
    filtered["rounds"] = filtered_rounds
    logger.info(f"[filter] Rounds: {len(rounds)} -> {len(filtered_rounds)}")

    # Filter kills
    kills = demo_data.get("kills", [])
    filtered_kills = [k for k in kills if first_round <= k.get("round_num", 0) <= last_round]
    filtered["kills"] = filtered_kills
    logger.info(f"[filter] Kills: {len(kills)} -> {len(filtered_kills)}")

    # Filter damages
    damages = demo_data.get("damages", [])
    filtered_damages = [d for d in damages if first_round <= d.get("round_num", 0) <= last_round]
    filtered["damages"] = filtered_damages

    # Filter grenades
    grenades = demo_data.get("grenades", [])
    filtered_grenades = [g for g in grenades if first_round <= g.get("round_num", 0) <= last_round]
    filtered["grenades"] = filtered_grenades

    # Filter bomb events
    bomb_events = demo_data.get("bomb_events", [])
    filtered_bomb = [b for b in bomb_events if first_round <= b.get("round_num", 0) <= last_round]
    filtered["bomb_events"] = filtered_bomb

    # Calculate video_start_tick - the tick where video begins
    # This is needed for accurate video timestamp calculations
    video_start_tick = None
    if filtered_rounds:
        first_round_data = filtered_rounds[0]
        # Use freeze_end of the first visible round as video start
        video_start_tick = first_round_data.get(
            "freeze_end_tick", first_round_data.get("start_tick", 0)
        )

    # Add metadata about the filtering
    filtered["video_rounds"] = {
        "first_round": first_round,
        "last_round": last_round,
        "total_rounds_in_video": len(filtered_rounds),
    }
    filtered["video_start_tick"] = video_start_tick

    # Update summary
    if "summary" in filtered:
        filtered["summary"]["video_rounds"] = filtered["video_rounds"]
        filtered["summary"]["rounds_played"] = len(filtered_rounds)

    return filtered


class PipelineOrchestrator:
    """
    Coordinates the 2-Agent Pipeline.

    Flow:
    1. Round Detector: Quick LLM call to detect which rounds are in the video
    2. Observer: Multi-angle analysis (generates 10-20 tips)
    3. Validator: Cross-check and confidence scoring

    Key features:
    - Simpler flow (2 agents)
    - Explicit confidence scoring
    - Clear verification criteria
    - Round detection to filter demo data
    """

    def __init__(
        self,
        video_file: Any,
        replay_data: dict,
        game_type: str,
        knowledge_base: str = "",
    ):
        """
        Initialize the orchestrator.

        Args:
            video_file: Gemini file object (already uploaded)
            replay_data: Parsed replay/demo data
            game_type: 'aoe2' or 'cs2'
            knowledge_base: Game-specific knowledge to inject
        """
        self.client = get_gemini_client()
        self.video_file = video_file
        self.replay_data = replay_data
        self.game_type = game_type
        self.knowledge_base = knowledge_base

    async def analyze(self) -> ProducerOutput:
        """
        Run the full analysis pipeline.

        Returns:
            ProducerOutput with all tips and metadata
        """
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("PIPELINE STARTING (2-Agent Architecture)")
        logger.info("=" * 60)
        logger.info(f"    Game type: {self.game_type.upper()}")
        logger.info(f"    Video: {self.video_file.name}")

        # ======================================================================
        # Step 0: Round Detection (CS2 only)
        # ======================================================================
        filtered_replay_data = self.replay_data
        round_detection_time = 0

        if self.game_type == "cs2":
            logger.info("\n" + "=" * 60)
            logger.info("[0/3] ROUND DETECTOR - Detecting rounds in video")
            logger.info("=" * 60)
            step_start = time.time()

            round_info = await detect_video_rounds(
                self.client,
                self.video_file,
                self.game_type,
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
        # Step 1: Observer - Multi-angle analysis
        # ======================================================================
        logger.info("\n" + "=" * 60)
        logger.info("[1/2] OBSERVER - Multi-Angle Analysis")
        logger.info("    Perspectives: Exploitable Patterns, Rank-Up Habits, Missed Adaptations")
        logger.info("=" * 60)
        step_start = time.time()

        observer = ObserverAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=filtered_replay_data,
            game_type=self.game_type,
            knowledge_base=self.knowledge_base,
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

        validator = ValidatorAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=filtered_replay_data,
            game_type=self.game_type,
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
            # Include round detection info
            "video_rounds": filtered_replay_data.get("video_rounds"),
            # Include raw observer output for debugging
            "observer_output": observer_output.model_dump(),
        })

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"    Total time: {total_time:.1f}s")
        if round_detection_time > 0:
            logger.info(f"    Round detection: {round_detection_time:.1f}s")
        logger.info(f"    Observer: {len(observer_output.tips)} tips in {observer_time:.1f}s")
        logger.info(f"    Validator: {len(final_output.tips)} tips verified in {validator_time:.1f}s")
        logger.info(f"    Final tips: {len(final_output.tips)}")
        logger.info("=" * 60)

        return final_output

    async def run_observer_only(self) -> Any:
        """Run only the Observer for testing."""
        logger.info("Running Observer only...")

        # Still do round detection for observer-only mode
        filtered_replay_data = self.replay_data

        if self.game_type == "cs2":
            round_info = await detect_video_rounds(
                self.client,
                self.video_file,
                self.game_type,
            )

            if round_info.get("detected"):
                filtered_replay_data = filter_demo_data_by_rounds(
                    self.replay_data,
                    round_info.get("first_round"),
                    round_info.get("last_round"),
                )

        observer = ObserverAgent(
            client=self.client,
            video_file=self.video_file,
            replay_data=filtered_replay_data,
            game_type=self.game_type,
            knowledge_base=self.knowledge_base,
        )

        output, _ = await observer.process({})
        return output


async def run_pipeline(
    video_path: str,
    replay_data: dict,
    game_type: str,
    knowledge_base: str = "",
) -> ProducerOutput:
    """
    Convenience function to run the full pipeline.

    Args:
        video_path: Path to video file (will be uploaded)
        replay_data: Parsed replay data
        game_type: 'aoe2' or 'cs2'
        knowledge_base: Game-specific knowledge

    Returns:
        ProducerOutput with tips and metadata
    """
    client = get_gemini_client()

    # Upload video
    logger.info(f"Uploading video: {video_path}")
    video_file = await upload_video_to_gemini(client, video_path)

    # Run pipeline
    orchestrator = PipelineOrchestrator(
        video_file=video_file,
        replay_data=replay_data,
        game_type=game_type,
        knowledge_base=knowledge_base,
    )

    result = await orchestrator.analyze()

    # Cleanup video file
    try:
        client.files.delete(name=video_file.name)
        logger.info(f"Deleted video file: {video_file.name}")
    except Exception as e:
        logger.warning(f"Failed to delete video file: {e}")

    return result
