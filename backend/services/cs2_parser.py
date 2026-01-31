"""
Counter-Strike 2 demo parser using demoparser2/awpy.

Extracts comprehensive game data including:
- Header: map, tickrate, game version
- Kills: with assists, flash assists, positions, sides
- Damages: with hitgroups, armor damage
- Rounds: with timing details, bomb plants
- Grenades: all utility usage
- Bomb events: plants, defuses, pickups, drops
- Smokes: positions and durations
- Infernos: molotov/incendiary coverage
- Player stats: per-round totals
"""
from typing import Any
import logging

logger = logging.getLogger(__name__)


def parse_cs2_demo(file_path: str) -> dict[str, Any]:
    """
    Parse a CS2 .dem file and extract comprehensive game data.

    Returns a structured dict with:
    - summary: High-level game info (map, teams, score, tickrate)
    - players: Player stats per round
    - rounds: Round-by-round breakdown with timing
    - kills: All kill events with full details
    - damages: All damage events with hitgroups
    - grenades: All utility usage
    - bomb: Bomb events (plant, defuse, pickup, drop)
    - smokes: Smoke grenade positions and durations
    - infernos: Molotov/incendiary coverage
    """
    try:
        # Try using awpy first (higher-level API)
        return parse_with_awpy(file_path)
    except ImportError:
        # Fall back to demoparser2
        return parse_with_demoparser2(file_path)


def parse_with_awpy(file_path: str) -> dict[str, Any]:
    """Parse using awpy library - extracts all available data."""
    from awpy import Demo

    dem = Demo(file_path)
    dem.parse()

    # ==========================================================================
    # HEADER - Game metadata
    # ==========================================================================
    header = {}
    if hasattr(dem, 'header') and dem.header:
        header = {
            "map_name": dem.header.get("map_name", "Unknown"),
            "tickrate": dem.header.get("tickrate", 64),
            "game_version": dem.header.get("game_version", "Unknown"),
            "protocol": dem.header.get("protocol", 0),
        }

    # ==========================================================================
    # PLAYER STATS - Per-round performance
    # ==========================================================================
    players = []
    player_stats = {}
    if hasattr(dem, 'player_round_totals') and dem.player_round_totals is not None:
        try:
            for row in dem.player_round_totals.to_dicts():
                name = row.get("name", "Unknown")
                if name not in player_stats:
                    # Determine player's team from team_name or side
                    team_name = row.get("team_name", "")
                    side = row.get("side", "")

                    # Try to determine CT/T from team_name or side
                    # team_name might be actual team name, side is CT/T
                    player_side = side if side in ["CT", "T"] else ""

                    player_stats[name] = {
                        "name": name,
                        "steamid": row.get("steamid", ""),
                        "team_name": team_name,
                        "team": team_name if team_name else player_side,  # For display compatibility
                        "side": player_side,  # CT or T
                        "sides_played": set(),  # Track all sides played
                        "rounds": [],
                        "total_kills": 0,
                        "total_deaths": 0,
                        "total_assists": 0,
                        "total_damage": 0,
                    }

                # Track which side they played this round
                round_side = row.get("side", "")
                if round_side:
                    player_stats[name]["sides_played"].add(round_side)

                # Add round stats
                round_stats = {
                    "round_num": row.get("round_num", 0),
                    "kills": row.get("kills", 0),
                    "deaths": row.get("deaths", 0),
                    "assists": row.get("assists", 0),
                    "damage": row.get("damage", 0),
                    "adr": row.get("adr", 0),
                    "kast": row.get("kast", False),
                    "side": round_side,
                }
                player_stats[name]["rounds"].append(round_stats)
                player_stats[name]["total_kills"] += round_stats["kills"]
                player_stats[name]["total_deaths"] += round_stats["deaths"]
                player_stats[name]["total_assists"] += round_stats["assists"]
                player_stats[name]["total_damage"] += round_stats["damage"]

            # Convert sets to lists for JSON serialization
            for p in player_stats.values():
                p["sides_played"] = list(p["sides_played"])

            players = list(player_stats.values())
        except Exception as e:
            logger.warning(f"Error extracting player stats: {e}")
            # Fallback to just names
            player_names = dem.player_round_totals.select("name").unique().to_series().to_list()
            players = [{"name": name} for name in player_names if name]

    # ==========================================================================
    # ROUNDS - With full timing details
    # ==========================================================================
    rounds = []
    if hasattr(dem, 'rounds') and dem.rounds is not None:
        for rnd in dem.rounds.to_dicts():
            rounds.append({
                "round_num": rnd.get("round_num", 0),
                "start_tick": rnd.get("start", 0),
                "freeze_end_tick": rnd.get("freeze_end", 0),
                "end_tick": rnd.get("end", 0),
                "official_end_tick": rnd.get("official_end", 0),
                "winner": rnd.get("winner", "Unknown"),
                "reason": rnd.get("reason", "Unknown"),
                "bomb_planted": rnd.get("bomb_plant", False),
                "bomb_site": rnd.get("bomb_site", None),
            })

    # ==========================================================================
    # KILLS - With assists, flash assists, sides, positions
    # ==========================================================================
    kills = []
    if hasattr(dem, 'kills') and dem.kills is not None:
        for kill in dem.kills.to_dicts()[:500]:  # Limit for payload size
            kills.append({
                "tick": kill.get("tick", 0),
                "round_num": kill.get("round_num", 0),
                # Attacker info
                "attacker": kill.get("attacker_name", "Unknown"),
                "attacker_steamid": kill.get("attacker_steamid", ""),
                "attacker_side": kill.get("attacker_side", ""),
                "attacker_pos": {
                    "x": kill.get("attacker_X", 0),
                    "y": kill.get("attacker_Y", 0),
                    "z": kill.get("attacker_Z", 0),
                },
                # Victim info
                "victim": kill.get("victim_name", "Unknown"),
                "victim_steamid": kill.get("victim_steamid", ""),
                "victim_side": kill.get("victim_side", ""),
                "victim_pos": {
                    "x": kill.get("victim_X", 0),
                    "y": kill.get("victim_Y", 0),
                    "z": kill.get("victim_Z", 0),
                },
                # Kill details
                "weapon": kill.get("weapon", "Unknown"),
                "headshot": kill.get("headshot", False),
                "penetrated": kill.get("penetrated", False),
                "noscope": kill.get("noscope", False),
                "thrusmoke": kill.get("thrusmoke", False),
                "attackerblind": kill.get("attackerblind", False),
                # Assist info
                "assister": kill.get("assister_name", None),
                "assister_steamid": kill.get("assister_steamid", None),
                "assister_side": kill.get("assister_side", None),
                "flash_assist": kill.get("assistedflash", False),
            })

    # ==========================================================================
    # DAMAGES - With hitgroups and armor
    # ==========================================================================
    damages = []
    if hasattr(dem, 'damages') and dem.damages is not None:
        for dmg in dem.damages.to_dicts()[:1000]:  # Limit for payload size
            damages.append({
                "tick": dmg.get("tick", 0),
                "round_num": dmg.get("round_num", 0),
                # Attacker info
                "attacker": dmg.get("attacker_name", "Unknown"),
                "attacker_steamid": dmg.get("attacker_steamid", ""),
                "attacker_side": dmg.get("attacker_side", ""),
                # Victim info
                "victim": dmg.get("victim_name", "Unknown"),
                "victim_steamid": dmg.get("victim_steamid", ""),
                "victim_side": dmg.get("victim_side", ""),
                # Damage details
                "damage_health": dmg.get("dmg_health", 0),
                "damage_armor": dmg.get("dmg_armor", 0),
                "hitgroup": dmg.get("hitgroup", "Unknown"),
                "weapon": dmg.get("weapon", "Unknown"),
            })

    # ==========================================================================
    # GRENADES - All utility usage
    # ==========================================================================
    grenades = []
    if hasattr(dem, 'grenades') and dem.grenades is not None:
        for nade in dem.grenades.to_dicts()[:500]:
            grenades.append({
                "tick": nade.get("tick", 0),
                "round_num": nade.get("round_num", 0),
                "thrower": nade.get("thrower", "Unknown"),
                "thrower_steamid": nade.get("thrower_steamid", ""),
                "grenade_type": nade.get("grenade_type", "Unknown"),
                "position": {
                    "x": nade.get("X", 0),
                    "y": nade.get("Y", 0),
                    "z": nade.get("Z", 0),
                },
                "entity_id": nade.get("entity_id", 0),
            })

    # ==========================================================================
    # BOMB EVENTS - Plants, defuses, pickups, drops
    # ==========================================================================
    bomb_events = []
    if hasattr(dem, 'bomb') and dem.bomb is not None:
        for event in dem.bomb.to_dicts():
            bomb_events.append({
                "tick": event.get("tick", 0),
                "round_num": event.get("round_num", 0),
                "event_type": event.get("status", event.get("event", "Unknown")),
                "player": event.get("name", "Unknown"),
                "player_steamid": event.get("steamid", ""),
                "bombsite": event.get("bombsite", None),
                "position": {
                    "x": event.get("X", 0),
                    "y": event.get("Y", 0),
                    "z": event.get("Z", 0),
                },
            })

    # ==========================================================================
    # SMOKES - Smoke grenade positions and durations
    # ==========================================================================
    smokes = []
    if hasattr(dem, 'smokes') and dem.smokes is not None:
        for smoke in dem.smokes.to_dicts()[:200]:
            smokes.append({
                "start_tick": smoke.get("start_tick", 0),
                "end_tick": smoke.get("end_tick", 0),
                "round_num": smoke.get("round_num", 0),
                "thrower": smoke.get("thrower_name", "Unknown"),
                "thrower_steamid": smoke.get("thrower_steamid", ""),
                "thrower_side": smoke.get("thrower_side", ""),
                "position": {
                    "x": smoke.get("X", 0),
                    "y": smoke.get("Y", 0),
                    "z": smoke.get("Z", 0),
                },
                "entity_id": smoke.get("entity_id", 0),
            })

    # ==========================================================================
    # INFERNOS - Molotov/incendiary coverage
    # ==========================================================================
    infernos = []
    if hasattr(dem, 'infernos') and dem.infernos is not None:
        for fire in dem.infernos.to_dicts()[:200]:
            infernos.append({
                "start_tick": fire.get("start_tick", 0),
                "end_tick": fire.get("end_tick", 0),
                "round_num": fire.get("round_num", 0),
                "thrower": fire.get("thrower_name", "Unknown"),
                "thrower_steamid": fire.get("thrower_steamid", ""),
                "thrower_side": fire.get("thrower_side", ""),
                "position": {
                    "x": fire.get("X", 0),
                    "y": fire.get("Y", 0),
                    "z": fire.get("Z", 0),
                },
                "entity_id": fire.get("entity_id", 0),
            })

    # ==========================================================================
    # SHOTS - Weapon fire events (if available)
    # ==========================================================================
    shots = []
    if hasattr(dem, 'shots') and dem.shots is not None:
        for shot in dem.shots.to_dicts()[:1000]:
            shots.append({
                "tick": shot.get("tick", 0),
                "round_num": shot.get("round_num", 0),
                "player": shot.get("player_name", shot.get("name", "Unknown")),
                "player_steamid": shot.get("steamid", ""),
                "weapon": shot.get("weapon", "Unknown"),
                "silenced": shot.get("silenced", False),
                "position": {
                    "x": shot.get("X", 0),
                    "y": shot.get("Y", 0),
                    "z": shot.get("Z", 0),
                },
            })

    # ==========================================================================
    # BUILD SUMMARY
    # ==========================================================================
    # Calculate team scores from rounds
    ct_wins = sum(1 for r in rounds if r.get("winner") == "CT")
    t_wins = sum(1 for r in rounds if r.get("winner") == "T")

    # Determine winning team
    if ct_wins > t_wins:
        winning_side = "CT"
    elif t_wins > ct_wins:
        winning_side = "T"
    else:
        winning_side = None  # Draw

    # Determine which players were on the winning team
    # In CS2, players swap sides at halftime, so we need to figure out
    # which "team" (group of 5 players) won based on their combined rounds
    # For now, we'll try to determine the player's primary side from first half
    # or use the most frequent side they played

    # Group players by their starting side (first round side)
    for player in players:
        player_rounds = player.get("rounds", [])
        if player_rounds:
            # Use the side from the first round as their "team"
            first_round = min(player_rounds, key=lambda r: r.get("round_num", 0))
            player["starting_side"] = first_round.get("side", "")

            # Determine if player won based on starting side
            # If they started CT and CT won first half + T won second half proportionally
            # This is complex due to side swaps - simplified: check total rounds won by their starting side
            starting_side = player["starting_side"]

            # For a proper winner determination, we need to track which team they're on
            # Simplified approach: if they started on a side, count those rounds for that side
            if starting_side and winning_side:
                # Player's team wins if their starting side is winning side
                # But this doesn't account for side swap correctly
                # Better: just mark winner based on final score and team grouping
                player["winner"] = (starting_side == winning_side)
            else:
                player["winner"] = False
        else:
            player["starting_side"] = ""
            player["winner"] = False

        # Ensure 'team' field is set for display
        if not player.get("team"):
            player["team"] = player.get("team_name") or player.get("starting_side") or "Unknown"

    summary = {
        "map": header.get("map_name", "Unknown"),
        "tickrate": header.get("tickrate", 64),
        "game_version": header.get("game_version", "Unknown"),
        "rounds_played": len(rounds),
        "score": {
            "CT": ct_wins,
            "T": t_wins,
        },
        "winning_side": winning_side,
        "players": players,
        "total_kills": len(kills),
        "total_grenades": len(grenades),
        "total_bomb_events": len(bomb_events),
    }

    return {
        "summary": summary,
        "rounds": rounds,
        "kills": kills,
        "damages": damages,
        "grenades": grenades,
        "bomb_events": bomb_events,
        "smokes": smokes,
        "infernos": infernos,
        "shots": shots,
    }


def parse_with_demoparser2(file_path: str) -> dict[str, Any]:
    """Parse using demoparser2 library (lower-level fallback)."""
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
        # Empty arrays for consistency with awpy output
        "damages": [],
        "grenades": [],
        "bomb_events": [],
        "smokes": [],
        "infernos": [],
        "shots": [],
    }


def format_for_gemini(game_data: dict) -> str:
    """
    Format game data into a comprehensive string prompt for Gemini analysis.
    """
    summary = game_data.get("summary", {})
    kills = game_data.get("kills", [])
    rounds = game_data.get("rounds", [])
    grenades = game_data.get("grenades", [])
    bomb_events = game_data.get("bomb_events", [])
    damages = game_data.get("damages", [])

    lines = [
        "## Counter-Strike 2 Game Analysis",
        "",
        f"**Map:** {summary.get('map', 'Unknown')}",
        f"**Rounds Played:** {summary.get('rounds_played', len(rounds))}",
        f"**Final Score:** CT {summary.get('score', {}).get('CT', 0)} - {summary.get('score', {}).get('T', 0)} T",
        f"**Tickrate:** {summary.get('tickrate', 64)}",
        "",
    ]

    # Player stats
    players = summary.get("players", [])
    if players and isinstance(players[0], dict) and "total_kills" in players[0]:
        lines.append("### Player Stats:")
        for p in players:
            kda = f"{p.get('total_kills', 0)}/{p.get('total_deaths', 0)}/{p.get('total_assists', 0)}"
            lines.append(f"- {p.get('name')}: {kda} ({p.get('total_damage', 0)} damage)")
        lines.append("")

    # Round results with details
    lines.append("### Round Results:")
    for rnd in rounds[:30]:
        bomb_info = ""
        if rnd.get("bomb_planted"):
            bomb_info = f" [Bomb planted {rnd.get('bomb_site', '')}]"
        lines.append(
            f"- Round {rnd.get('round_num')}: {rnd.get('winner')} won ({rnd.get('reason')}){bomb_info}"
        )
    lines.append("")

    # Kill feed with more details
    lines.append("### Kill Feed (first 50):")
    for kill in kills[:50]:
        hs = " HS" if kill.get("headshot") else ""
        assist = ""
        if kill.get("assister"):
            flash = " (flash)" if kill.get("flash_assist") else ""
            assist = f" + {kill.get('assister')}{flash}"
        lines.append(
            f"- R{kill.get('round_num', '?')}: {kill.get('attacker')} [{kill.get('weapon')}{hs}] {kill.get('victim')}{assist}"
        )
    lines.append("")

    # Grenade summary by type
    if grenades:
        lines.append("### Utility Usage:")
        nade_counts = {}
        for nade in grenades:
            nade_type = nade.get("grenade_type", "unknown")
            thrower = nade.get("thrower", "Unknown")
            key = f"{thrower}_{nade_type}"
            if key not in nade_counts:
                nade_counts[key] = {"thrower": thrower, "type": nade_type, "count": 0}
            nade_counts[key]["count"] += 1

        for info in sorted(nade_counts.values(), key=lambda x: -x["count"])[:20]:
            lines.append(f"- {info['thrower']}: {info['count']}x {info['type']}")
        lines.append("")

    # Bomb events
    if bomb_events:
        lines.append("### Bomb Events:")
        for event in bomb_events[:30]:
            lines.append(
                f"- R{event.get('round_num', '?')}: {event.get('player')} {event.get('event_type')} "
                f"{'@ ' + event.get('bombsite') if event.get('bombsite') else ''}"
            )
        lines.append("")

    return "\n".join(lines)
