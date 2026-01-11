"""
Age of Empires II replay parser using mgz library.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def parse_aoe2_replay(file_path: str) -> dict[str, Any]:
    """
    Parse an AoE2 .aoe2record file and extract game data.

    Returns a structured dict with:
    - summary: High-level game info (map, players, winner, duration)
    - players: Detailed player info (civ, rating, uptime, eapm)
    - actions: Key actions for analysis
    """
    from mgz.model import parse_match, serialize

    logger.info(f"Parsing replay: {file_path}")

    with open(file_path, "rb") as f:
        match = parse_match(f)
        raw_data = serialize(match)

    # Extract uptimes (indexed by player number)
    raw_uptimes = raw_data.get("uptimes", [])
    player_uptimes = {}
    for uptime in raw_uptimes:
        player_num = uptime.get("player")
        age = uptime.get("age", "").lower().replace(" ", "_")
        timestamp = _parse_timestamp(uptime.get("timestamp", "0:00:00"))
        if player_num not in player_uptimes:
            player_uptimes[player_num] = {}
        player_uptimes[player_num][f"{age}_age"] = timestamp

    # Extract player info
    players = []
    for player in raw_data.get("players", []):
        player_num = player.get("number")
        players.append({
            "name": player.get("name", "Unknown"),
            "civilization": player.get("civilization", "Unknown"),
            "color": player.get("color", "Unknown"),
            "winner": player.get("winner", False),
            "rating": player.get("rate_snapshot", 0),
            "eapm": player.get("eapm", 0),
            "uptime": player_uptimes.get(player_num, {}),
        })

    # Build summary
    duration_str = raw_data.get("duration", "0:00:00")
    duration_seconds = _parse_duration(duration_str)
    summary = {
        "map": raw_data.get("map", {}).get("name", "Unknown"),
        "map_size": raw_data.get("map", {}).get("size", "Unknown"),
        "duration": _format_duration(duration_seconds),
        "game_version": raw_data.get("game_version", "Unknown"),
        "rated": raw_data.get("rated", False),
        "players": players,
    }

    # Extract key actions
    raw_actions = raw_data.get("actions", [])
    actions = _extract_key_actions(raw_actions)

    logger.info(f"Parsed {len(players)} players, {len(actions)} key actions")

    return {
        "summary": summary,
        "players": players,
        "actions": actions,
    }


def _extract_key_actions(actions: list) -> list[dict]:
    """Extract key actions (builds, queues, orders)."""
    key_actions = []
    important_types = {"BUILD", "DE_QUEUE", "GAME", "ORDER"}

    for action in actions[:500]:
        action_type = action.get("type", "")
        if action_type in important_types:
            key_actions.append({
                "time": action.get("timestamp", "0:00:00"),
                "player": action.get("player", 0),
                "type": action_type,
                "details": action.get("payload", {})
            })

    return key_actions


def _parse_duration(duration_str: str) -> int:
    """Parse duration string like '0:33:50.899000' to seconds."""
    if not duration_str or not isinstance(duration_str, str):
        return 0
    try:
        parts = duration_str.split(":")
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return int(hours * 3600 + minutes * 60 + seconds)
        return 0
    except (ValueError, IndexError):
        return 0


def _parse_timestamp(ts: str) -> int:
    """Parse timestamp string to seconds."""
    return _parse_duration(ts)


def _format_duration(seconds: int) -> str:
    """Format seconds to mm:ss or h:mm:ss if over an hour."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


def format_for_gemini(game_data: dict) -> str:
    """Format game data for LLM analysis."""
    summary = game_data.get("summary", {})
    players = game_data.get("players", [])
    actions = game_data.get("actions", [])

    lines = [
        f"## Age of Empires II Game",
        f"**Map:** {summary.get('map', 'Unknown')} ({summary.get('map_size', 'Unknown')})",
        f"**Duration:** {summary.get('duration', '0:00')}",
        "",
        "### Players:",
    ]

    for p in players:
        status = "WINNER" if p.get("winner") else "LOSER"
        lines.append(
            f"- **{p.get('name')}** ({p.get('civilization')}) - "
            f"Rating: {p.get('rating', 'Unrated')}, "
            f"eAPM: {p.get('eapm', 0)}, {status}"
        )

        uptime = p.get("uptime", {})
        if uptime:
            for age in ["feudal_age", "castle_age", "imperial_age"]:
                if age in uptime:
                    lines.append(f"  - {age.replace('_', ' ').title()}: {_format_duration(uptime[age])}")

    lines.append("")
    lines.append("### Key Actions (first 30):")

    for action in actions[:30]:
        time_sec = _parse_timestamp(action.get("time", "0:00:00"))
        details = action.get("details", {})
        detail_str = details.get("command", "") or details.get("name", "") or ""
        lines.append(f"- [{_format_duration(time_sec)}] P{action.get('player')}: {action.get('type')} {detail_str}")

    return "\n".join(lines)
