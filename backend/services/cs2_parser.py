"""
Counter-Strike 2 demo parser using demoparser2/awpy.
"""
from typing import Any


def parse_cs2_demo(file_path: str) -> dict[str, Any]:
    """
    Parse a CS2 .dem file and extract game data.

    Returns a structured dict with:
    - summary: High-level game info (map, teams, score)
    - players: Player stats (K/D/A, ADR, etc.)
    - rounds: Round-by-round breakdown
    - kills: All kill events with details
    """
    try:
        # Try using awpy first (higher-level API)
        return parse_with_awpy(file_path)
    except ImportError:
        # Fall back to demoparser2
        return parse_with_demoparser2(file_path)


def parse_with_awpy(file_path: str) -> dict[str, Any]:
    """Parse using awpy library."""
    from awpy import Demo

    dem = Demo(file_path)
    dem.parse()

    # Extract player names from player_round_totals
    players = []
    if hasattr(dem, 'player_round_totals') and dem.player_round_totals is not None:
        # Get unique player names
        player_names = dem.player_round_totals.select("name").unique().to_series().to_list()
        players = [{"name": name} for name in player_names if name]

    # Extract summary
    summary = {
        "map": dem.header.get("map_name", "Unknown") if hasattr(dem, 'header') else "Unknown",
        "rounds_played": len(dem.rounds) if hasattr(dem, 'rounds') and dem.rounds is not None else 0,
        "players": players,
    }

    # Extract kills data (dem.kills is a polars DataFrame)
    kills = []
    if hasattr(dem, 'kills') and dem.kills is not None:
        for kill in dem.kills.to_dicts()[:500]:  # Limit for payload size
            kills.append({
                "tick": kill.get("tick", 0),
                "attacker": kill.get("attacker_name", "Unknown"),
                "victim": kill.get("victim_name", "Unknown"),
                "weapon": kill.get("weapon", "Unknown"),
                "headshot": kill.get("headshot", False),
                "attacker_pos": {
                    "x": kill.get("attacker_X", 0),
                    "y": kill.get("attacker_Y", 0),
                    "z": kill.get("attacker_Z", 0),
                },
                "victim_pos": {
                    "x": kill.get("victim_X", 0),
                    "y": kill.get("victim_Y", 0),
                    "z": kill.get("victim_Z", 0),
                },
            })

    # Extract damage data (dem.damages is a polars DataFrame)
    damages = []
    if hasattr(dem, 'damages') and dem.damages is not None:
        for dmg in dem.damages.to_dicts()[:1000]:
            damages.append({
                "tick": dmg.get("tick", 0),
                "attacker": dmg.get("attacker_name", "Unknown"),
                "victim": dmg.get("victim_name", "Unknown"),
                "damage": dmg.get("dmg_health", 0),
                "weapon": dmg.get("weapon", "Unknown"),
            })

    # Extract round data (dem.rounds is a polars DataFrame)
    rounds = []
    if hasattr(dem, 'rounds') and dem.rounds is not None:
        for rnd in dem.rounds.to_dicts():
            rounds.append({
                "round_num": rnd.get("round_num", 0),
                "winner": rnd.get("winner", "Unknown"),
                "reason": rnd.get("reason", "Unknown"),
            })

    return {
        "summary": summary,
        "kills": kills,
        "damages": damages,
        "rounds": rounds,
    }


def parse_with_demoparser2(file_path: str) -> dict[str, Any]:
    """Parse using demoparser2 library (lower-level)."""
    from demoparser2 import DemoParser

    parser = DemoParser(file_path)

    # Parse player deaths (kills)
    try:
        kills_df = parser.parse_event(
            "player_death",
            player=["X", "Y", "Z", "last_place_name"],
            other=["headshot", "weapon", "total_rounds_played"]
        )
        kills = kills_df.to_dict(orient='records') if kills_df is not None else []
    except Exception:
        kills = []

    # Parse round ends
    try:
        rounds_df = parser.parse_event("round_end")
        rounds = rounds_df.to_dict(orient='records') if rounds_df is not None else []
    except Exception:
        rounds = []

    # Get player positions at regular intervals
    try:
        ticks_df = parser.parse_ticks(
            ["X", "Y", "Z", "health", "armor_value", "team_num"],
            ticks=[i * 128 for i in range(100)]  # Sample every 128 ticks
        )
        positions = ticks_df.to_dict(orient='records') if ticks_df is not None else []
    except Exception:
        positions = []

    summary = {
        "total_kills": len(kills),
        "total_rounds": len(rounds),
    }

    return {
        "summary": summary,
        "kills": kills[:500],
        "rounds": rounds,
        "positions": positions[:1000],
    }


def format_for_gemini(game_data: dict) -> str:
    """
    Format game data into a string prompt for Gemini analysis.
    """
    summary = game_data.get("summary", {})
    kills = game_data.get("kills", [])
    rounds = game_data.get("rounds", [])

    lines = [
        "## Counter-Strike 2 Game Analysis",
        "",
        f"**Map:** {summary.get('map', 'Unknown')}",
        f"**Rounds Played:** {summary.get('rounds_played', len(rounds))}",
        "",
        "### Kill Feed (first 50):",
    ]

    for kill in kills[:50]:
        hs = " (HEADSHOT)" if kill.get("headshot") else ""
        lines.append(
            f"- {kill.get('attacker')} killed {kill.get('victim')} "
            f"with {kill.get('weapon')}{hs}"
        )

    lines.append("")
    lines.append("### Round Results:")

    for rnd in rounds[:30]:
        lines.append(
            f"- Round {rnd.get('round_num')}: {rnd.get('winner')} won ({rnd.get('reason')})"
        )

    return "\n".join(lines)
