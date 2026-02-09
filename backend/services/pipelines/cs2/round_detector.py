"""
Round detection for CS2 videos.

Detects which rounds are shown in the video by analyzing the HUD.
This allows filtering demo data to only include relevant rounds.
Also provides deterministic round timeline building from demo data.
"""

import json
import logging
import os
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


async def detect_video_rounds(
    client: genai.Client,
    video_file: Any,
) -> dict:
    """
    Quick LLM call to detect which rounds are shown in the video.

    Args:
        client: Gemini client
        video_file: Uploaded video file

    Returns:
        Dict with 'first_round', 'last_round', and 'detected' keys
    """
    logger.info("[round_detector] Detecting rounds in video...")

    prompt = """Analyze this CS2 gameplay video to identify the round numbers shown.

## HOW TO FIND THE ROUND NUMBER

In CS2, the round number appears in the HUD:
1. **Top center of screen**: During freeze time/buy phase, it says "Round X" clearly
2. **Score display**: The score at top shows "X - Y" and current round = X + Y + 1
3. **Killfeed area**: Sometimes shows round number
4. **Scoreboard (TAB)**: Shows current round prominently

## YOUR TASK

1. Watch the FIRST 15 seconds of the video carefully
   - Look for "Round X" text during freeze time
   - Check the score display (e.g., "0-0" means round 1, "2-1" means round 4)
   - Note the first round number you can confirm

2. Watch the LAST 15 seconds of the video
   - Look for the final round being played
   - Check the score display to calculate round number
   - Note the last round number you can confirm

3. If you see score "A - B" in the HUD, the current round is A + B + 1

Return ONLY this JSON (no other text):
{"first_round": X, "last_round": Y}

Examples:
- Video starts mid-match with score 3-2: {"first_round": 6, "last_round": ...}
- Video starts at beginning: {"first_round": 1, "last_round": ...}
- Can't determine last round: {"first_round": 1, "last_round": null}
"""

    try:
        # Use a fast model for this quick detection
        model = os.getenv("GEMINI_FAST_MODEL", "gemini-3-flash-preview")

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

        logger.info(
            f"[round_detector] Response in {elapsed:.1f}s: {response_text[:200]}"
        )

        # Extract JSON from response
        json_match = re.search(r"\{[^}]+\}", response_text)
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
            logger.warning("[round_detector] Could not parse JSON from response")
            return {"first_round": None, "last_round": None, "detected": False}

    except Exception as e:
        logger.error(f"[round_detector] Error detecting rounds: {e}")
        return {
            "first_round": None,
            "last_round": None,
            "detected": False,
            "error": str(e),
        }


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
    filtered_rounds = [
        r for r in rounds if first_round <= r.get("round_num", 0) <= last_round
    ]
    filtered["rounds"] = filtered_rounds
    logger.info(f"[filter] Rounds: {len(rounds)} -> {len(filtered_rounds)}")

    # Filter kills
    kills = demo_data.get("kills", [])
    filtered_kills = [
        k for k in kills if first_round <= k.get("round_num", 0) <= last_round
    ]
    filtered["kills"] = filtered_kills
    logger.info(f"[filter] Kills: {len(kills)} -> {len(filtered_kills)}")

    # Filter damages
    damages = demo_data.get("damages", [])
    filtered_damages = [
        d for d in damages if first_round <= d.get("round_num", 0) <= last_round
    ]
    filtered["damages"] = filtered_damages

    # Filter grenades
    grenades = demo_data.get("grenades", [])
    filtered_grenades = [
        g for g in grenades if first_round <= g.get("round_num", 0) <= last_round
    ]
    filtered["grenades"] = filtered_grenades

    # Filter bomb events
    bomb_events = demo_data.get("bomb_events", [])
    filtered_bomb = [
        b for b in bomb_events if first_round <= b.get("round_num", 0) <= last_round
    ]
    filtered["bomb_events"] = filtered_bomb

    # Calculate video_start_tick - the tick where video begins
    # This is needed for accurate video timestamp calculations
    video_start_tick = None
    if filtered_rounds:
        first_round_data = filtered_rounds[0]
        # Use start_tick of the first visible round as video start (includes buy phase)
        video_start_tick = first_round_data.get("start_tick", 0)

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


def build_rounds_timeline_from_demo(
    demo_data: dict,
    pov_player: Optional[str] = None,
) -> list[dict]:
    """
    Build rounds timeline from demo data (deterministic).

    Uses demo tick data and tickrate to calculate video timestamps.
    Includes death timestamps and win/loss status for POV player per round.

    Args:
        demo_data: Demo data (filtered or full)
        pov_player: Name of the POV player (for death detection and win/loss)

    Returns:
        List of round timeline dicts with start/end/death timestamps and win/loss status
    """
    summary = demo_data.get("summary", {})
    rounds = demo_data.get("rounds", [])
    kills = demo_data.get("kills", [])
    players = summary.get("players", [])
    tickrate = summary.get("tickrate", 64)

    if not rounds:
        logger.warning("[GAME-ANALYSIS] [build_rounds_timeline] No rounds data available")
        return []

    # video_start_tick is set by filter_demo_data_by_rounds
    video_start_tick = demo_data.get("video_start_tick")
    if video_start_tick is None:
        # Fallback: use first round's start_tick (includes buy phase)
        first_round = rounds[0]
        video_start_tick = first_round.get("start_tick", 0)
        logger.info(
            f"[GAME-ANALYSIS] [build_rounds_timeline] No video_start_tick set, "
            f"using first round start_tick: {video_start_tick}"
        )

    # Get POV player name from demo data if not provided
    if pov_player is None:
        pov_player = demo_data.get("pov_player")

    # Find POV player's starting side (CT or T), normalized to uppercase
    pov_starting_side = None
    if pov_player:
        pov_lower = pov_player.lower()
        for player in players:
            if player.get("name", "").lower() == pov_lower:
                side = player.get("starting_side", "")
                pov_starting_side = side.upper() if side else None
                break

    logger.info(f"[GAME-ANALYSIS] [build_rounds_timeline] POV player {pov_player} starting side: {pov_starting_side}")

    # Build death lookup for POV player (round_num -> death_tick)
    death_by_round: dict[int, int] = {}
    if pov_player:
        pov_lower = pov_player.lower()
        for kill in kills:
            victim = kill.get("victim") or ""
            if victim.lower() == pov_lower:
                round_num = kill.get("round_num", 0)
                death_tick = kill.get("tick", 0)
                # Only keep first death per round (shouldn't be multiple, but just in case)
                if round_num not in death_by_round:
                    death_by_round[round_num] = death_tick

    logger.info(
        f"[GAME-ANALYSIS] [build_rounds_timeline] Building timeline for {len(rounds)} rounds, "
        f"pov_player={pov_player}, deaths={len(death_by_round)}"
    )

    timeline = []
    for rnd in rounds:
        round_num = rnd.get("round_num", 0)
        start_tick = rnd.get("start_tick") or 0
        end_tick = rnd.get("end_tick") or 0
        round_winner_raw = rnd.get("winner") or ""
        round_winner = round_winner_raw.upper() if round_winner_raw else None

        # Calculate video timestamps (seconds from video start)
        start_seconds = max(0.0, (start_tick - video_start_tick) / tickrate)
        end_seconds = max(0.0, (end_tick - video_start_tick) / tickrate)

        # Format display times (M:SS)
        start_time = f"{int(start_seconds // 60)}:{int(start_seconds % 60):02d}"
        end_time = f"{int(end_seconds // 60)}:{int(end_seconds % 60):02d}"

        # Check for POV player death in this round
        death_tick = death_by_round.get(round_num)
        if death_tick:
            death_seconds = max(0.0, (death_tick - video_start_tick) / tickrate)
            death_time = f"{int(death_seconds // 60)}:{int(death_seconds % 60):02d}"
        else:
            death_seconds = None
            death_time = None

        # Determine win/loss status based on round winner and POV player's side
        # In CS2, sides swap at halftime (typically after round 12)
        # First half: rounds 1-12, Second half: rounds 13+
        status = "unknown"
        if pov_starting_side and round_winner:
            # Determine POV player's side for this round (account for side swap)
            if round_num <= 12:
                pov_side_this_round = pov_starting_side
            else:
                # After halftime, sides are swapped
                pov_side_this_round = "T" if pov_starting_side == "CT" else "CT"

            # Compare round winner to POV player's side
            if round_winner == pov_side_this_round:
                status = "win"
            else:
                status = "loss"

        timeline.append({
            "round": round_num,
            "start_seconds": start_seconds,
            "start_time": start_time,
            "end_seconds": end_seconds,
            "end_time": end_time,
            "death_seconds": death_seconds,
            "death_time": death_time,
            "status": status,
        })

    logger.info(f"[GAME-ANALYSIS] [build_rounds_timeline] Built timeline with {len(timeline)} rounds")

    return timeline
