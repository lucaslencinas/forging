"""
CS2 video analysis service using Gemini's multimodal capabilities.
Analyzes gameplay videos combined with demo data for timestamped coaching tips.
"""
import json
import logging
import os
import re
from typing import Optional

from models import TimestampedTip, VideoAnalysisResponse, GameSummary, Player, PlayerUptime
from services.gcs import download_to_temp
from services.llm.gemini import GeminiProvider
from services.cs2_knowledge import CS2_KNOWLEDGE

logger = logging.getLogger(__name__)


# System prompt for CS2 coaching
CS2_VIDEO_SYSTEM_PROMPT = """You are an expert Counter-Strike 2 coach with FaceIT Level 10 / Global Elite experience.
You are analyzing gameplay footage to provide specific, actionable coaching tips.

## VIDEO CONTEXT

IMPORTANT - PARTIAL MATCH RECORDINGS:
- The video may only contain 1 or a few rounds, NOT the full match
- Look at the SCOREBOARD at the top of the screen to identify which round(s) are being played
- Match the score shown in the video with the demo data to understand context
- Example: If scoreboard shows "CT 5 - 3 T", this is Round 9

TIMESTAMP ALIGNMENT:
- Your timestamps should be VIDEO timestamps (from the start of the video)
- CS2 demos use ticks (128 per second typically)
- Focus on what you SEE in the video, not what the demo says happened

## ANALYSIS APPROACH

For each moment you identify:
1. What did the player do?
2. What should they have done instead?
3. Why does this matter? (consequence of the mistake)

## KEY COACHING AREAS

**Crosshair Placement:**
- Is crosshair at head level?
- Are they pre-aiming common angles?
- Are they clearing angles one at a time?

**Utility Usage:**
- Are they using utility before peeking?
- Are flashes timed correctly (pop flashes vs. early)?
- Are smokes blocking useful angles?
- Are they saving utility for too long?

**Positioning:**
- Are they overexposed to multiple angles?
- Are they holding off-angles or predictable spots?
- Are they jiggle-peeking to gather info?
- Are they counter-strafing before shooting?

**Economy:**
- Did they buy correctly for the situation?
- Are they saving on eco rounds?
- Did they drop for teammates when needed?

**Team Play:**
- Are they trading kills?
- Are they communicating positions?
- Are they supporting teammates?

## CATEGORIES

Use these categories for tips:
- aim: Crosshair placement, spray control, flick accuracy
- utility: Smoke, flash, molotov, HE grenade usage
- positioning: Angles, movement, peeking, rotations
- economy: Buy decisions, saving, drops
- teamwork: Trading, coordination, communication

Be specific about what you see. Don't guess - only comment on what's clearly visible."""


def _build_cs2_video_prompt(demo_data: Optional[dict] = None) -> str:
    """Build the prompt for CS2 video analysis, optionally including demo data."""
    prompt_parts = []

    # Include demo data if provided
    if demo_data:
        summary = demo_data.get("summary", {})
        kills = demo_data.get("kills", [])
        rounds = demo_data.get("rounds", [])

        prompt_parts.append("=" * 60)
        prompt_parts.append("DEMO DATA (USE TO IDENTIFY WHICH ROUND(S) THE VIDEO SHOWS)")
        prompt_parts.append("=" * 60)
        prompt_parts.append(f"Map: {summary.get('map', 'Unknown')}")
        prompt_parts.append(f"Total Rounds: {summary.get('rounds_played', len(rounds))}")
        prompt_parts.append("")

        # Round results for context
        if rounds:
            prompt_parts.append("### Round Results:")
            for rnd in rounds[:30]:
                round_num = rnd.get("round_num", 0)
                winner = rnd.get("winner", "Unknown")
                reason = rnd.get("reason", "Unknown")
                prompt_parts.append(f"  Round {round_num}: {winner} won ({reason})")
            prompt_parts.append("")

        # Kill summary by round for cross-referencing
        if kills:
            prompt_parts.append("### Key Kills (use to match with video):")
            # Group kills by round if we have tick info
            for i, kill in enumerate(kills[:30]):
                hs = " [HS]" if kill.get("headshot") else ""
                weapon = kill.get("weapon", "unknown")
                prompt_parts.append(
                    f"  {kill.get('attacker', 'Unknown')} killed {kill.get('victim', 'Unknown')} "
                    f"with {weapon}{hs}"
                )
            prompt_parts.append("")

        prompt_parts.append("=" * 60)
        prompt_parts.append("IMPORTANT: The video may show only 1-3 rounds of the match.")
        prompt_parts.append("Look at the scoreboard (top of screen) to identify which round(s).")
        prompt_parts.append("Match kills you see with the demo data above for context.")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")

    # Add CS2 strategic knowledge
    prompt_parts.append(CS2_KNOWLEDGE)
    prompt_parts.append("")

    # Main task
    prompt_parts.extend([
        "TASK: Watch this Counter-Strike 2 gameplay video and provide 5-10 timestamped coaching tips.",
        "",
        "## ANALYSIS STEPS",
        "",
        "STEP 1 - Identify the round(s) shown:",
        "- Look at the scoreboard at the top of the screen",
        "- Note the current score (e.g., CT 5 - 3 T = Round 9)",
        "- Cross-reference with demo data if available",
        "",
        "STEP 2 - Watch for key moments:",
        "- Crosshair placement issues",
        "- Missed utility opportunities",
        "- Positioning mistakes",
        "- Economic decisions",
        "- Trade/teamwork issues",
        "",
        "STEP 3 - For each tip, provide:",
        "- Exact VIDEO timestamp (MM:SS)",
        "- Category (aim, utility, positioning, economy, teamwork)",
        "- Specific observation and recommendation",
        "",
        "## OUTPUT FORMAT",
        "",
        "Format your response as JSON:",
        "{",
        '  "identified_rounds": "Round 9-11 (CT 5-3 to CT 7-4)",',
        '  "tips": [',
        '    {"timestamp": "0:15", "category": "aim", "tip": "Your description..."},',
        '    {"timestamp": "0:42", "category": "utility", "tip": "Your description..."},',
        "    ...",
        "  ]",
        "}",
        "",
        "IMPORTANT: Return ONLY valid JSON, no other text."
    ])

    return "\n".join(prompt_parts)


def _parse_timestamp(ts: str) -> int:
    """Parse MM:SS or H:MM:SS to seconds."""
    parts = ts.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def _parse_tips_from_response(content: str) -> list[TimestampedTip]:
    """Parse the LLM response into TimestampedTip objects."""
    tips = []

    try:
        # Find JSON in the response (may be wrapped in markdown code blocks)
        json_match = re.search(r'\{[\s\S]*"tips"[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())
            raw_tips = data.get("tips", [])

            for tip in raw_tips:
                timestamp_str = tip.get("timestamp", "0:00")
                tips.append(TimestampedTip(
                    timestamp_seconds=_parse_timestamp(timestamp_str),
                    timestamp_display=timestamp_str,
                    tip=tip.get("tip", ""),
                    category=tip.get("category", "positioning")
                ))
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse tips JSON: {e}")

    return tips


def _build_cs2_game_summary(demo_data: Optional[dict]) -> Optional[GameSummary]:
    """Build GameSummary from CS2 demo data if available."""
    if not demo_data:
        return None

    summary = demo_data.get("summary", {})

    # CS2 doesn't have the same player structure as AoE2
    # Create a minimal summary
    return GameSummary(
        map=summary.get("map", "Unknown"),
        map_size="",  # Not applicable for CS2
        duration=f"{summary.get('rounds_played', 0)} rounds",
        game_version="CS2",
        rated=False,
        players=[]  # Would need to parse player data from kills/damages
    )


async def analyze_cs2_video(
    video_object_name: str,
    demo_data: Optional[dict] = None,
    duration_seconds: int = 0,
    model: Optional[str] = None,
) -> VideoAnalysisResponse:
    """
    Analyze a CS2 gameplay video using Gemini's multimodal capabilities.

    Args:
        video_object_name: GCS object name for the video (already uploaded)
        demo_data: Optional parsed demo data for richer context
        duration_seconds: Video duration in seconds (for response)
        model: Optional model name to use for analysis

    Returns:
        VideoAnalysisResponse with timestamped coaching tips
    """
    gemini = GeminiProvider()
    temp_video_path = None
    gemini_file_name = None

    try:
        # Step 1: Download video from GCS to temp file
        logger.info(f"Downloading video from GCS: {video_object_name}")
        temp_video_path = download_to_temp(video_object_name)

        # Step 2: Upload to Gemini File API
        logger.info("Uploading video to Gemini File API...")
        gemini_file_name = gemini.upload_video(temp_video_path)

        # Step 3: Build prompt with optional demo data
        prompt = _build_cs2_video_prompt(demo_data)

        # Step 4: Analyze with Gemini
        logger.info(f"Analyzing CS2 video with Gemini (model: {model or 'default'})...")
        result = await gemini.analyze_video(
            file_name=gemini_file_name,
            prompt=prompt,
            system_prompt=CS2_VIDEO_SYSTEM_PROMPT,
            model=model
        )

        if not result.success:
            return VideoAnalysisResponse(
                video_object_name=video_object_name,
                duration_seconds=duration_seconds,
                tips=[],
                game_summary=_build_cs2_game_summary(demo_data),
                model_used=result.model,
                provider=result.provider,
                error=result.error
            )

        # Step 5: Parse tips from response
        tips = _parse_tips_from_response(result.content)
        logger.info(f"Parsed {len(tips)} coaching tips from response")

        return VideoAnalysisResponse(
            video_object_name=video_object_name,
            duration_seconds=duration_seconds,
            tips=tips,
            game_summary=_build_cs2_game_summary(demo_data),
            model_used=result.model,
            provider=result.provider
        )

    except Exception as e:
        logger.error(f"CS2 video analysis failed: {e}")
        return VideoAnalysisResponse(
            video_object_name=video_object_name,
            duration_seconds=duration_seconds,
            tips=[],
            game_summary=_build_cs2_game_summary(demo_data),
            model_used="unknown",
            provider="gemini",
            error=str(e)
        )

    finally:
        # Cleanup: Delete temp file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Cleaned up temp file: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")

        # Cleanup: Delete Gemini file (optional, they auto-delete after 48h)
        if gemini_file_name:
            gemini.delete_video(gemini_file_name)
