"""
Video analysis service using Gemini's multimodal capabilities.
Analyzes gameplay videos combined with replay data for timestamped coaching tips.
"""
import json
import logging
import os
import re
import subprocess
from typing import Any, Optional

from models import TimestampedTip, VideoAnalysisResponse, GameSummary, Player, PlayerUptime
from services.gcs import download_to_temp
from services.llm.gemini import GeminiProvider
from services.aoe2_knowledge import AOE2_KNOWLEDGE

logger = logging.getLogger(__name__)


# System prompt for AoE2 coaching
AOE2_VIDEO_SYSTEM_PROMPT = """You are an expert Age of Empires II: Definitive Edition coach with 2000+ ELO.
You are analyzing gameplay footage to provide specific, actionable coaching tips.

## TIMESTAMP RULES

CRITICAL - GAME SPEED CONVERSION:
- The replay data uses GAME TIME (runs faster than real time)
- The video uses REAL TIME
- Standard/Normal speed: Game time = Real time × 1.5
- To convert: Real time = Game time ÷ 1.5
- Example: Game time 9:00 = Real time 6:00

CRITICAL - VIDEO ALIGNMENT:
- The video may start BEFORE the game begins (loading screens)
- Find when the in-game timer shows 0:00 - that's your reference point
- All your timestamps should be VIDEO timestamps (real time)

## THINK ABOUT CAUSE AND CONSEQUENCE

Before giving a tip, analyze:
1. What is the player doing?
2. Why might they be doing it? (could be intentional)
3. What are the consequences of this action/inaction?
4. What would a better alternative be?

Example analysis:
- Observation: Scout is standing still near deer for 10 seconds
- Context: This is deer luring - scout pushes deer toward TC
- Consequence: Delays scouting enemy base
- Trade-off: If opponent is doing M@A rush, deer luring without scouting first is risky
- Tip: "While deer luring is efficient, you missed scouting the enemy Barracks built at 4:26. Earlier scouting would have revealed the M@A rush."

## RULES

1. ONLY describe what you can CLEARLY SEE in the video
2. Use REPLAY DATA as ground truth for what happened (units, buildings, research)
3. Distinguish intentional play from mistakes
4. Focus on impactful mistakes, not minor micro issues
5. Consider opponent's actions when giving advice

## CATEGORIES
- economy: Villager idle time, TC idle, resource management, build order issues
- military: Unit control, army positioning, engagements, raid defense
- strategy: Scouting, decision making, adaptation, timing

Identify unit types carefully - militia vs men-at-arms vs eagles look different."""


def _calculate_tip_count(duration_seconds: int) -> tuple[int, int]:
    """
    Calculate the recommended number of tips based on video duration.

    Based on observation:
    - 15 min AoE2 videos get ~8 tips
    - Shorter CS2 videos (< 5 min) benefit from more tips due to fast-paced action
    - Longer videos (30 min) should scale up proportionally

    Returns:
        Tuple of (min_tips, max_tips)
    """
    duration_minutes = duration_seconds / 60

    if duration_minutes <= 5:
        # Short videos (CS2 rounds): 5-8 tips for fast-paced action
        return (5, 8)
    elif duration_minutes <= 10:
        # Medium videos: 6-10 tips
        return (6, 10)
    elif duration_minutes <= 15:
        # Standard videos: 8-12 tips
        return (8, 12)
    elif duration_minutes <= 20:
        # Longer videos: 10-15 tips
        return (10, 15)
    elif duration_minutes <= 30:
        # Very long videos: 12-18 tips
        return (12, 18)
    else:
        # Extra long videos (30+ min): 15-20 tips
        return (15, 20)


def _build_video_analysis_prompt(replay_data: Optional[dict] = None, duration_seconds: int = 0) -> str:
    """Build the prompt for video analysis, optionally including replay data."""
    prompt_parts = []

    # Calculate dynamic tip count based on video duration
    min_tips, max_tips = _calculate_tip_count(duration_seconds)

    # Include replay data if provided
    if replay_data:
        summary = replay_data.get("summary", {})
        players = summary.get("players", [])
        player_stats = replay_data.get("player_stats", {})

        prompt_parts.append("=" * 60)
        prompt_parts.append("REPLAY DATA (THIS IS GROUND TRUTH - DO NOT CONTRADICT)")
        prompt_parts.append("=" * 60)
        prompt_parts.append(f"Map: {summary.get('map', 'Unknown')} ({summary.get('map_size', 'Unknown')})")
        prompt_parts.append(f"Game Duration: {summary.get('duration', 'Unknown')} (game time)")
        prompt_parts.append(f"Real Duration: {summary.get('duration_real', 'Unknown')} (video time)")
        prompt_parts.append(f"Game Speed: {summary.get('game_speed', 'Standard')} (multiplier: {summary.get('speed_multiplier', 1.5)}x)")
        prompt_parts.append("")
        prompt_parts.append("NOTE: All timestamps below are in GAME TIME. Divide by 1.5 to get VIDEO time.")
        prompt_parts.append("")

        # Player info with stats
        for p in players:
            player_num = None
            # Find player number from name
            for pnum, stats in player_stats.items():
                if pnum == 1 and p.get("name") == players[0].get("name"):
                    player_num = 1
                    break
                elif pnum == 2 and len(players) > 1 and p.get("name") == players[1].get("name"):
                    player_num = 2
                    break

            winner_str = "[WINNER]" if p.get("winner") else "[LOSER]"
            prompt_parts.append(f"### Player: {p.get('name')} ({p.get('civilization')}) {winner_str}")
            prompt_parts.append(f"    Rating: {p.get('rating', 'Unrated')}, eAPM: {p.get('eapm', 0)}")

            uptime = p.get("uptime", {})
            if uptime.get("feudal_age"):
                prompt_parts.append(f"    Feudal Age at: {_format_seconds(uptime['feudal_age'])}")
            if uptime.get("castle_age"):
                prompt_parts.append(f"    Castle Age at: {_format_seconds(uptime['castle_age'])}")
            if uptime.get("imperial_age"):
                prompt_parts.append(f"    Imperial Age at: {_format_seconds(uptime['imperial_age'])}")

            # Add player-specific stats
            if player_num and player_num in player_stats:
                stats = player_stats[player_num]

                # Units trained
                units = stats.get("units_trained", {})
                if units:
                    units_str = ", ".join(f"{count}x {unit}" for unit, count in units.items())
                    prompt_parts.append(f"    Units trained: {units_str}")

                # Buildings built
                buildings = stats.get("buildings_built", [])
                if buildings:
                    buildings_str = ", ".join(f"{b['building']} ({b['time']})" for b in buildings[:12])
                    prompt_parts.append(f"    Buildings: {buildings_str}")

                # Researches
                researches = stats.get("researches", [])
                if researches:
                    research_str = ", ".join(f"{r['technology']} ({r['time']})" for r in researches)
                    prompt_parts.append(f"    Researches: {research_str}")

            prompt_parts.append("")

        prompt_parts.append("=" * 60)
        prompt_parts.append("CRITICAL: The data above is FACT from the replay file.")
        prompt_parts.append("- If 'Tower' is not listed in buildings, there was NO tower rush")
        prompt_parts.append("- If 'Militia' is listed, that's what was trained - not guessing")
        prompt_parts.append("- Use this data to understand what ACTUALLY happened")
        prompt_parts.append("=" * 60)
        prompt_parts.append("")

    # Add AOE2 strategic knowledge
    prompt_parts.append(AOE2_KNOWLEDGE)
    prompt_parts.append("")

    # Main task
    prompt_parts.extend([
        f"TASK: Watch this Age of Empires 2 gameplay video and provide {min_tips}-{max_tips} timestamped coaching tips.",
        "",
        "## ANALYSIS APPROACH",
        "",
        "STEP 1 - Identify what happened in the game:",
        "- Look at REPLAY DATA to see what units/buildings each player made",
        "- Identify the strategies used (M@A rush, scouts, archers, etc.)",
        "",
        "STEP 2 - Watch the video and note key moments:",
        "- When did the player get attacked? How did they respond?",
        "- Were there idle units/buildings?",
        "- Did they scout the enemy's strategy?",
        "",
        "STEP 3 - Analyze cause and consequence:",
        "- For each issue, think: WHY did this happen? WHAT was the consequence?",
        "- Consider if actions were INTENTIONAL (deer luring, army positioning)",
        "- Focus on mistakes that COST THE PLAYER THE GAME",
        "",
        "## TIMESTAMP CONVERSION",
        "- REPLAY timestamps are in GAME TIME (1.5x speed)",
        "- VIDEO timestamps are in REAL TIME",
        "- Divide game time by 1.5 to get video time",
        "- Example: Game time 6:00 = Video time 4:00",
        "",
        "## TIP QUALITY",
        "Each tip should:",
        "1. Reference a specific VIDEO timestamp (MM:SS)",
        "2. Describe what you observed",
        "3. Explain the CONSEQUENCE of the action/inaction",
        "4. Suggest what should have been done instead",
        "",
        "Good tip example:",
        '"At 3:30, you are deer luring but have not scouted enemy base. The opponent built a Barracks at 4:26 (game time ~2:50 video time) for a M@A rush. Earlier scouting would have revealed this and let you prepare."',
        "",
        "## OUTPUT FORMAT",
        "",
        "Format your response as JSON:",
        "{",
        '  "game_start_offset": "0:12",',
        '  "tips": [',
        '    {"timestamp": "2:17", "category": "economy", "tip": "Your description with cause and consequence..."},',
        '    {"timestamp": "5:42", "category": "strategy", "tip": "Your description with cause and consequence..."},',
        "    ...",
        "  ]",
        "}",
        "",
        "The game_start_offset is when the actual match begins in the video (in-game timer shows 0:00).",
        "All tip timestamps must be VIDEO timestamps (real time, not game time).",
        "",
        "IMPORTANT: Return ONLY valid JSON, no other text."
    ])

    return "\n".join(prompt_parts)


def _format_seconds(seconds: int) -> str:
    """Format seconds to MM:SS."""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"


def _get_video_duration(video_path: str) -> int:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return int(duration)
    except Exception as e:
        logger.warning(f"Failed to get video duration: {e}")
    return 0


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

    # Try to extract JSON from the response
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
                    category=tip.get("category", "strategy")
                ))
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning(f"Failed to parse tips JSON: {e}")

    return tips


def _build_game_summary(replay_data: Optional[dict] = None) -> Optional[GameSummary]:
    """Build GameSummary from replay data."""
    if not replay_data:
        return None

    summary = replay_data.get("summary", {})
    players_data = summary.get("players", [])

    players = []
    for p in players_data:
        uptime = p.get("uptime", {})
        players.append(Player(
            name=p.get("name", "Unknown"),
            civilization=p.get("civilization", "Unknown"),
            color=p.get("color", "Unknown"),
            winner=p.get("winner", False),
            rating=p.get("rating", 0),
            eapm=p.get("eapm", 0),
            uptime=PlayerUptime(
                feudal_age=uptime.get("feudal_age"),
                castle_age=uptime.get("castle_age"),
                imperial_age=uptime.get("imperial_age")
            )
        ))

    return GameSummary(
        map=summary.get("map", "Unknown"),
        map_size=summary.get("map_size", "Unknown"),
        duration=summary.get("duration", "0:00"),
        game_version=summary.get("game_version", "Unknown"),
        rated=summary.get("rated", False),
        players=players
    )


async def analyze_video(
    video_object_name: str,
    replay_data: Optional[dict] = None,
    duration_seconds: int = 0,
    model: Optional[str] = None,
) -> VideoAnalysisResponse:
    """
    Analyze a gameplay video using Gemini's multimodal capabilities.

    Args:
        video_object_name: GCS object name for the video (already uploaded)
        replay_data: Parsed replay data (required for game metadata)
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

        # Step 3: Build prompt with replay data and duration for dynamic tip count
        prompt = _build_video_analysis_prompt(replay_data, duration_seconds)

        # Step 4: Analyze with Gemini
        logger.info(f"Analyzing video with Gemini (model: {model or 'default'})...")
        result = await gemini.analyze_video(
            file_name=gemini_file_name,
            prompt=prompt,
            system_prompt=AOE2_VIDEO_SYSTEM_PROMPT,
            model=model,
            video_path=temp_video_path  # Allow re-upload on API key rotation
        )

        # Track the actual file name (may change if re-uploaded on key rotation)
        actual_file_name = result.file_name if result.file_name else gemini_file_name

        if not result.success:
            # Cleanup before returning
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception:
                    pass
            if actual_file_name:
                gemini.delete_video(actual_file_name)
            return VideoAnalysisResponse(
                video_object_name=video_object_name,
                duration_seconds=duration_seconds,
                tips=[],
                game_summary=_build_game_summary(replay_data),
                model_used=result.model,
                provider=result.provider,
                error=result.error
            )

        # Step 5: Parse tips from response
        tips = _parse_tips_from_response(result.content)
        logger.info(f"Parsed {len(tips)} coaching tips from response")

        # Cleanup
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Cleaned up temp file: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
        if actual_file_name:
            gemini.delete_video(actual_file_name)

        return VideoAnalysisResponse(
            video_object_name=video_object_name,
            duration_seconds=duration_seconds,
            tips=tips,
            game_summary=_build_game_summary(replay_data),
            model_used=result.model,
            provider=result.provider
        )

    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        # Cleanup on exception
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except Exception:
                pass
        if gemini_file_name:
            gemini.delete_video(gemini_file_name)
        return VideoAnalysisResponse(
            video_object_name=video_object_name,
            duration_seconds=duration_seconds,
            tips=[],
            game_summary=_build_game_summary(replay_data),
            model_used="unknown",
            provider="gemini",
            error=str(e)
        )
