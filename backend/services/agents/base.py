"""
Base class for Pipeline Agents using Gemini 3 Interactions API.

All agents inherit from BaseAgent and implement:
- get_system_prompt(): Agent's personality and instructions
- build_prompt(): Construct the user prompt from input data
- parse_response(): Parse LLM response into structured output
"""

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from google import genai
from google.genai import types  # Used for file upload

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all Pipeline agents.

    Uses Gemini 3's Interactions API for:
    - Server-managed conversation state (via previous_interaction_id)
    - Thinking levels for deeper reasoning
    - Thought signatures for context preservation
    """

    # Override in subclasses
    name: str = "base"
    uses_video: bool = False
    thinking_level: str = "low"  # minimal, low, medium, high
    include_thoughts: bool = False  # Expose reasoning (useful for demo)

    def __init__(
        self,
        client: genai.Client,
        video_file: Optional[Any] = None,
        replay_data: Optional[dict] = None,
        game_type: str = "aoe2",
        knowledge_base: str = "",
    ):
        """
        Initialize a Pipeline Agent.

        Args:
            client: Gemini client instance (shared across agents)
            video_file: Gemini file object (already uploaded)
            replay_data: Parsed replay/demo data
            game_type: 'aoe2' or 'cs2'
            knowledge_base: Game-specific knowledge to inject into prompts
        """
        self.client = client
        self.video_file = video_file
        self.replay_data = replay_data or {}
        self.game_type = game_type
        self.knowledge_base = knowledge_base

        # Stored after processing
        self.last_thoughts: Optional[str] = None
        self.last_interaction_id: Optional[str] = None
        self.last_raw_response: Optional[str] = None

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        This defines the agent's personality, role, and instructions.
        """
        pass

    @abstractmethod
    def build_prompt(self, input_data: dict) -> str:
        """
        Build the user prompt from input data.

        Args:
            input_data: Data from previous agents in the pipeline

        Returns:
            The prompt to send to the model
        """
        pass

    @abstractmethod
    def parse_response(self, response_text: str, input_data: dict) -> Any:
        """
        Parse the LLM response into structured output.

        Args:
            response_text: Raw text response from the model
            input_data: Original input data (for context)

        Returns:
            Pydantic model instance (e.g., ObserverOutput, VerifierOutput)
        """
        pass

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from response text, handling markdown code blocks."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    async def process(
        self,
        input_data: dict,
        previous_interaction_id: Optional[str] = None,
    ) -> Tuple[Any, str]:
        """
        Execute the agent's task using Gemini Interactions API.

        Args:
            input_data: Data from previous agents
            previous_interaction_id: ID to chain from previous agent

        Returns:
            Tuple of (parsed_output, interaction_id) for chaining to next agent
        """
        system_prompt = self.get_system_prompt()
        user_prompt = self.build_prompt(input_data)

        # Log prompt sizes for debugging context usage
        logger.info(
            f"[{self.name}] Processing with thinking_level={self.thinking_level}"
        )
        logger.info(f"[{self.name}] System prompt: {len(system_prompt)} chars")
        logger.info(f"[{self.name}] User prompt: {len(user_prompt)} chars")
        logger.info(
            f"[{self.name}] Uses video: {self.uses_video and self.video_file is not None}"
        )
        if previous_interaction_id:
            logger.info(
                f"[{self.name}] Chaining from previous interaction (context may accumulate)"
            )

        # Build generation config with thinking level
        generation_config = {
            "thinking_level": self.thinking_level,
        }

        # Build input content
        # Interactions API requires explicit type fields
        if self.uses_video and self.video_file:
            input_content = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "video",
                    "uri": self.video_file.uri,
                    "mime_type": "video/mp4",
                },
            ]
            logger.info(
                f"[{self.name}] Including video in request: {self.video_file.uri}"
            )
        else:
            input_content = [{"type": "text", "text": user_prompt}]

        try:
            import asyncio

            # Create interaction (chains to previous if provided)
            if previous_interaction_id:
                logger.info(
                    f"[{self.name}] Chaining from interaction: {previous_interaction_id[:20]}..."
                )

            # Run synchronous API call in thread pool to avoid blocking event loop
            def _sync_create_interaction():
                return self.client.interactions.create(
                    model=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
                    input=input_content,
                    system_instruction=system_prompt,
                    generation_config=generation_config,
                    previous_interaction_id=previous_interaction_id,
                )

            interaction = await asyncio.to_thread(_sync_create_interaction)

            # Debug: log available attributes
            logger.debug(f"[{self.name}] Interaction attributes: {dir(interaction)}")

            # Extract response - try different attribute names
            response_text = ""

            # Try 'outputs' (plural) first - based on docs showing interaction.outputs[-1].text
            if hasattr(interaction, "outputs") and interaction.outputs:
                last_output = interaction.outputs[-1]
                if hasattr(last_output, "text"):
                    response_text = last_output.text
                elif hasattr(last_output, "parts"):
                    for part in last_output.parts:
                        if hasattr(part, "text"):
                            response_text += part.text
            # Try 'output' (singular)
            elif hasattr(interaction, "output") and interaction.output:
                if hasattr(interaction.output, "text"):
                    response_text = interaction.output.text
                elif hasattr(interaction.output, "parts"):
                    for part in interaction.output.parts:
                        if hasattr(part, "text"):
                            response_text += part.text
            # Try 'response'
            elif hasattr(interaction, "response") and interaction.response:
                if hasattr(interaction.response, "text"):
                    response_text = interaction.response.text
            # Try 'text' directly
            elif hasattr(interaction, "text"):
                response_text = interaction.text

            if not response_text:
                logger.warning(
                    f"[{self.name}] Could not extract text. Interaction: {interaction}"
                )

            self.last_raw_response = response_text
            self.last_interaction_id = interaction.id

            # Extract thoughts if available
            if hasattr(interaction, "thoughts") and interaction.thoughts:
                self.last_thoughts = str(interaction.thoughts)
                logger.info(f"[{self.name}] Captured reasoning thoughts")

            logger.info(f"[{self.name}] Got response ({len(response_text)} chars)")

            # Parse response
            parsed = self.parse_response(response_text, input_data)

            return parsed, interaction.id

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            raise

    def format_replay_data_for_prompt(self) -> str:
        """Format replay data based on game type."""
        if not self.replay_data:
            return "No replay data available."

        if self.game_type == "aoe2":
            return self._format_aoe2_replay()
        elif self.game_type == "cs2":
            return self._format_cs2_replay()
        else:
            return self._format_generic_replay()

    def _format_aoe2_replay(self) -> str:
        """Format AoE2 replay data with POV player clearly identified."""
        summary = self.replay_data.get("summary", {})
        players = summary.get("players", [])
        player_stats = self.replay_data.get("player_stats", {})
        actions = self.replay_data.get("actions", [])
        pov_player = self.replay_data.get("pov_player")

        lines = [
            "=" * 60,
            "AGE OF EMPIRES II - REPLAY DATA",
            "=" * 60,
            f"Map: {summary.get('map', 'Unknown')} ({summary.get('map_size', 'Unknown')})",
            f"Duration: {summary.get('duration', 'Unknown')} (game time)",
            f"Game Speed: {summary.get('game_speed', 'Normal')}",
            "",
        ]

        # POV player identification - CRITICAL section
        if pov_player:
            # Find POV player details
            pov_player_data = None
            pov_player_num = None
            for i, p in enumerate(players):
                if p.get("name", "").lower() == pov_player.lower():
                    pov_player_data = p
                    pov_player_num = i + 1
                    break

            lines.extend([
                "=" * 60,
                f"POV PLAYER: {pov_player}",
                "=" * 60,
                "",
                "CRITICAL: You are coaching THIS player. ALL tips must be about their gameplay.",
                "Do NOT give tips about what their opponent did.",
                "",
            ])

            if pov_player_data:
                lines.extend([
                    f"POV Player Details:",
                    f"  Name: {pov_player_data.get('name')}",
                    f"  Civilization: {pov_player_data.get('civilization', 'Unknown')}",
                    f"  Color: {pov_player_data.get('color', 'Unknown')}",
                    f"  Result: {'WON' if pov_player_data.get('winner') else 'LOST'}",
                ])

                # Add age uptimes for POV player
                uptime = pov_player_data.get("uptime", {})
                if uptime:
                    feudal = uptime.get("feudal_age") or uptime.get("feudal_age_age")
                    castle = uptime.get("castle_age") or uptime.get("castle_age_age")
                    imperial = uptime.get("imperial_age") or uptime.get("imperial_age_age")
                    if feudal:
                        lines.append(f"  Feudal Age: {feudal // 60}:{feudal % 60:02d}")
                    if castle:
                        lines.append(f"  Castle Age: {castle // 60}:{castle % 60:02d}")
                    if imperial:
                        lines.append(f"  Imperial Age: {imperial // 60}:{imperial % 60:02d}")
                lines.append("")

        lines.extend([
            "-" * 60,
            "ALL PLAYERS IN THIS GAME:",
            "-" * 60,
        ])

        # List all players with their details
        for i, p in enumerate(players):
            player_num = i + 1
            is_pov = pov_player and p.get("name", "").lower() == pov_player.lower()
            pov_marker = " <<< POV PLAYER (coaching this player)" if is_pov else ""
            winner_str = "[WINNER]" if p.get("winner") else "[LOSER]"
            civ = p.get("civilization", "Unknown")
            color = p.get("color", "Unknown")
            rating = p.get("rating", "Unrated")
            eapm = p.get("eapm", 0)

            lines.append(f"  Player {player_num}: {p.get('name', 'Unknown')}{pov_marker}")
            lines.append(f"    Civilization: {civ}")
            lines.append(f"    Color: {color}")
            lines.append(f"    Rating: {rating}, eAPM: {eapm}")
            lines.append(f"    Result: {winner_str}")

            # Add age uptimes
            uptime = p.get("uptime", {})
            if uptime:
                uptime_parts = []
                # Handle both "feudal_age" and "feudal_age_age" key formats
                for age_key in ["feudal_age", "feudal_age_age", "castle_age", "castle_age_age", "imperial_age", "imperial_age_age"]:
                    if age_key in uptime:
                        age_name = age_key.replace("_age_age", "").replace("_age", "").title()
                        seconds = uptime[age_key]
                        mins = seconds // 60
                        secs = seconds % 60
                        uptime_parts.append(f"{age_name}: {mins}:{secs:02d}")
                # Remove duplicates (in case both formats exist)
                seen = set()
                unique_parts = []
                for part in uptime_parts:
                    age_name = part.split(":")[0]
                    if age_name not in seen:
                        seen.add(age_name)
                        unique_parts.append(part)
                if unique_parts:
                    lines.append(f"    Age Times: {', '.join(unique_parts)}")
            lines.append("")

        # Key differences between players (for context, not identification)
        if len(players) >= 2:
            p1 = players[0]
            p2 = players[1]
            p1_stats = player_stats.get(1, {})
            p2_stats = player_stats.get(2, {})

            lines.extend([
                "-" * 60,
                "KEY DIFFERENCES BETWEEN PLAYERS:",
                "-" * 60,
            ])

            # Civilization difference
            lines.append(f"  - {p1.get('name', 'P1')} ({p1.get('color', '?')}) plays {p1.get('civilization', '?')}")
            lines.append(f"  - {p2.get('name', 'P2')} ({p2.get('color', '?')}) plays {p2.get('civilization', '?')}")

            # Key unit differences
            p1_units = p1_stats.get("units_trained", {})
            p2_units = p2_stats.get("units_trained", {})
            p1_military = [u for u in p1_units.keys() if u != "Villager"]
            p2_military = [u for u in p2_units.keys() if u != "Villager"]
            if p1_military or p2_military:
                p1_mil_str = ", ".join(p1_military[:3]) if p1_military else "none"
                p2_mil_str = ", ".join(p2_military[:3]) if p2_military else "none"
                lines.append(f"  - {p1.get('name', 'P1')} trained: {p1_mil_str}")
                lines.append(f"  - {p2.get('name', 'P2')} trained: {p2_mil_str}")

            # Winner/loser
            if p1.get("winner"):
                lines.append(f"  - {p1.get('name', 'P1')} WON the game")
            else:
                lines.append(f"  - {p2.get('name', 'P2')} WON the game")

        lines.append("")

        # Player statistics from replay
        if player_stats:
            lines.extend([
                "-" * 60,
                "PLAYER STATISTICS (from replay):",
                "-" * 60,
            ])
            for player_num, stats in sorted(player_stats.items()):
                # Find player name and check if POV
                player_name = "Unknown"
                is_pov = False
                for i, p in enumerate(players):
                    if i + 1 == player_num:
                        player_name = p.get("name", "Unknown")
                        is_pov = pov_player and player_name.lower() == pov_player.lower()
                        break

                pov_marker = " <<< POV PLAYER" if is_pov else ""
                lines.append(f"\n  Player {player_num} ({player_name}){pov_marker}:")

                # Units trained
                units = stats.get("units_trained", {})
                if units:
                    sorted_units = sorted(units.items(), key=lambda x: x[1], reverse=True)
                    unit_strs = [f"{name}: {count}" for name, count in sorted_units[:10]]
                    lines.append(f"    Units: {', '.join(unit_strs)}")

                # Buildings built
                buildings = stats.get("buildings_built", [])
                if buildings:
                    building_strs = [f"{b['building']} ({b['time']})" for b in buildings[:15]]
                    lines.append(f"    Buildings: {', '.join(building_strs)}")

                # Researches
                researches = stats.get("researches", [])
                if researches:
                    research_strs = [f"{r['technology']} ({r['time']})" for r in researches[:10]]
                    lines.append(f"    Researches: {', '.join(research_strs)}")

        # Key actions (limited to avoid overwhelming)
        if actions:
            lines.extend([
                "",
                "-" * 60,
                f"KEY ACTIONS ({len(actions)} total, showing first 50):",
                "-" * 60,
                "(P1, P2 = Player 1, Player 2 from the list above)",
            ])
            for action in actions[:50]:
                time_str = action.get("time", "0:00:00")[:7]  # Truncate to mm:ss
                player = action.get("player", 0)
                action_type = action.get("type", "UNKNOWN")
                details = action.get("details", {})

                # Build detail string
                detail_parts = []
                for key in ["building", "unit", "technology", "command"]:
                    if key in details and details[key]:
                        detail_parts.append(str(details[key]))
                detail_str = " ".join(detail_parts)

                lines.append(f"  [{time_str}] P{player}: {action_type} {detail_str}")

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    def _format_cs2_replay(self) -> str:
        """Format CS2 demo data with player identification guidance."""
        summary = self.replay_data.get("summary", {})
        players = summary.get("players", [])
        rounds = self.replay_data.get("rounds", [])
        kills = self.replay_data.get("kills", [])
        tickrate = summary.get("tickrate", 64)

        score = summary.get("score", {})
        ct_score = score.get("CT", 0)
        t_score = score.get("T", 0)
        winning_side = summary.get("winning_side", "")

        # Determine winner text
        if winning_side == "CT":
            winner_text = f"CT WINS ({ct_score}-{t_score})"
        elif winning_side == "T":
            winner_text = f"T WINS ({t_score}-{ct_score})"
        else:
            winner_text = f"DRAW ({ct_score}-{t_score})"

        # Try to identify POV player from replay_data metadata
        pov_player = self.replay_data.get("pov_player", None)

        lines = [
            "=" * 60,
            "COUNTER-STRIKE 2 - DEMO DATA",
            "=" * 60,
            f"Map: {summary.get('map', 'Unknown')}",
            f"Rounds: {summary.get('rounds_played', len(rounds))}",
            f"Final Score: CT {ct_score} - {t_score} T",
            f"Result: {winner_text}",
            f"Tickrate: {tickrate}",
            "",
        ]

        # POV player identification and death timeline
        if pov_player:
            lines.extend([
                "=" * 60,
                f"POV PLAYER: {pov_player}",
                "=" * 60,
                "",
                "CRITICAL: Only analyze gameplay while this player is ALIVE.",
                "Once they die, the view switches to spectating teammates - IGNORE that footage.",
                "",
            ])

            # Build complete round timeline with death info
            round_timeline = self._build_round_timeline(pov_player, kills, rounds, tickrate)
            if round_timeline:
                lines.extend([
                    "-" * 60,
                    f"ROUND TIMELINE FOR {pov_player}:",
                    "-" * 60,
                    "",
                    "Use this to know EXACTLY when tips are valid:",
                    "",
                ])
                for rnd in round_timeline:
                    round_num = rnd["round"]
                    start = rnd["start_time"]
                    end = rnd["end_time"]
                    status = rnd["status"]
                    valid_range = rnd["valid_range"]

                    lines.append(f"  Round {round_num}:")
                    lines.append(f"    Video time: {start} - {end}")
                    lines.append(f"    Status: {status}")
                    lines.append(f"    VALID TIP RANGE: {valid_range}")
                    if rnd["death_time"]:
                        lines.append(f"    -> Tips after {rnd['death_time']} are INVALID (spectating)")
                    lines.append("")

                # Log the timeline for debugging
                logger.info(f"[cs2_replay] POV Player: {pov_player}")
                for rnd in round_timeline:
                    if rnd["death_time"]:
                        logger.info(
                            f"[cs2_replay] Round {rnd['round']}: "
                            f"{rnd['start_time']}-{rnd['end_time']}, "
                            f"DIED at {rnd['death_time']}"
                        )
                    else:
                        logger.info(
                            f"[cs2_replay] Round {rnd['round']}: "
                            f"{rnd['start_time']}-{rnd['end_time']}, SURVIVED"
                        )
        else:
            lines.extend([
                "-" * 60,
                "THIS IS A FIRST-PERSON RECORDING:",
                "-" * 60,
                "The crosshair, HUD, and first-person view belong to the POV player.",
                "Identify them by:",
                "- Their name in the HUD or on the scoreboard",
                "- The weapons they are holding and using",
                "- The perspective you see is THEIR perspective",
                "",
            ])

        # Group players by starting side (first half side)
        ct_starters = []  # Players who started on CT side
        t_starters = []   # Players who started on T side
        unknown_side = []

        for p in players:
            starting_side = p.get("starting_side", "")
            if starting_side == "CT":
                ct_starters.append(p)
            elif starting_side == "T":
                t_starters.append(p)
            else:
                unknown_side.append(p)

        # Show players grouped by starting side with winner indicator
        lines.extend([
            "-" * 60,
            "PLAYERS (grouped by starting side):",
            "-" * 60,
        ])

        if ct_starters:
            ct_won = winning_side == "CT"
            ct_label = "Team 1 (Started CT)" + (" [WINNERS]" if ct_won else " [LOSERS]")
            lines.append(f"  {ct_label}:")
            for p in ct_starters:
                k = p.get("total_kills", 0)
                d = p.get("total_deaths", 0)
                a = p.get("total_assists", 0)
                dmg = p.get("total_damage", 0)
                lines.append(f"    - {p.get('name', 'Unknown')}: {k}K/{d}D/{a}A ({dmg} dmg)")

        if t_starters:
            t_won = winning_side == "T"
            t_label = "Team 2 (Started T)" + (" [WINNERS]" if t_won else " [LOSERS]")
            lines.append(f"  {t_label}:")
            for p in t_starters:
                k = p.get("total_kills", 0)
                d = p.get("total_deaths", 0)
                a = p.get("total_assists", 0)
                dmg = p.get("total_damage", 0)
                lines.append(f"    - {p.get('name', 'Unknown')}: {k}K/{d}D/{a}A ({dmg} dmg)")

        if unknown_side:
            lines.append("  Unknown team:")
            for p in unknown_side:
                k = p.get("total_kills", 0)
                d = p.get("total_deaths", 0)
                a = p.get("total_assists", 0)
                dmg = p.get("total_damage", 0)
                lines.append(f"    - {p.get('name', 'Unknown')}: {k}K/{d}D/{a}A ({dmg} dmg)")

        lines.append("")

        # Round results
        if rounds:
            lines.extend([
                "-" * 60,
                f"ROUND RESULTS ({len(rounds)} rounds):",
                "-" * 60,
            ])
            for rnd in rounds[:30]:
                bomb_info = ""
                if rnd.get("bomb_planted"):
                    site = rnd.get("bomb_site", "")
                    bomb_info = f" [Bomb @ {site}]" if site else " [Bomb planted]"
                lines.append(
                    f"  Round {rnd.get('round_num', '?')}: {rnd.get('winner', '?')} won "
                    f"({rnd.get('reason', 'unknown')}){bomb_info}"
                )
            lines.append("")

        # Key kills
        if kills:
            lines.extend([
                "-" * 60,
                f"KEY KILLS (first 30 of {len(kills)}):",
                "-" * 60,
            ])
            for kill in kills[:30]:
                hs = " HS" if kill.get("headshot") else ""
                weapon = kill.get("weapon", "?")
                attacker = kill.get("attacker", "?")
                victim = kill.get("victim", "?")
                rnd = kill.get("round_num", "?")

                assist_info = ""
                if kill.get("assister"):
                    flash = " (flash)" if kill.get("flash_assist") else ""
                    assist_info = f" + {kill.get('assister')}{flash}"

                lines.append(f"  R{rnd}: {attacker} [{weapon}{hs}] {victim}{assist_info}")

        # POV Player Actions Section (authoritative data for verification)
        if pov_player:
            pov_actions_section = self._build_pov_actions_section(
                pov_player, kills, rounds, tickrate
            )
            if pov_actions_section:
                lines.extend(pov_actions_section)

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    def _build_pov_actions_section(
        self,
        pov_player: str,
        kills: list,
        rounds: list,
        tickrate: int,
    ) -> list:
        """
        Build a section listing all POV player's actions from demo data.

        This is AUTHORITATIVE data - use for verification.
        """
        # Combine all grenade sources: grenades, smokes, and infernos
        grenades = list(self.replay_data.get("grenades", []))
        smokes = self.replay_data.get("smokes", [])
        infernos = self.replay_data.get("infernos", [])

        # Normalize smokes to grenade format
        for smoke in smokes:
            grenades.append({
                "tick": smoke.get("start_tick", 0),
                "round_num": smoke.get("round_num", 0),
                "thrower": smoke.get("thrower", ""),
                "grenade_type": "smokegrenade",
            })

        # Normalize infernos to grenade format
        for inferno in infernos:
            grenades.append({
                "tick": inferno.get("start_tick", 0),
                "round_num": inferno.get("round_num", 0),
                "thrower": inferno.get("thrower", ""),
                "grenade_type": "molotov",
            })

        damages = self.replay_data.get("damages", [])
        bomb_events = self.replay_data.get("bomb_events", [])

        # Use video_start_tick if available
        first_round_start = self.replay_data.get("video_start_tick")
        if first_round_start is None and rounds:
            first_round_start = rounds[0].get("freeze_end_tick") or rounds[0].get("start_tick") or 0
        if first_round_start is None:
            first_round_start = 0

        def tick_to_video_time(tick: int) -> str:
            tick = tick or 0
            video_seconds = max(0, (tick - first_round_start) / tickrate) if tickrate else 0
            mins = int(video_seconds // 60)
            secs = int(video_seconds % 60)
            return f"{mins}:{secs:02d}"

        lines = [
            "",
            "=" * 60,
            f"POV PLAYER ACTIONS - AUTHORITATIVE DATA",
            "=" * 60,
            "",
            "Use this to VERIFY tips. Only the POV player's own actions are valid tip subjects.",
            "If a tip references an action not listed here, it's about a teammate (REJECT).",
            "",
        ]

        # Build per-round data
        round_nums = sorted(set(r.get("round_num", 0) for r in rounds))

        for round_num in round_nums:
            round_lines = [f"  ROUND {round_num}:"]

            # POV player kills this round
            pov_kills = [
                k for k in kills
                if k.get("round_num") == round_num
                and (k.get("attacker") or "").lower() == pov_player.lower()
            ]
            if pov_kills:
                for k in pov_kills:
                    time_str = tick_to_video_time(k.get("tick", 0))
                    victim = k.get("victim", "?")
                    weapon = k.get("weapon", "?")
                    hs = " (headshot)" if k.get("headshot") else ""
                    round_lines.append(f"    KILL @ {time_str}: killed {victim} with {weapon}{hs}")
            else:
                round_lines.append("    KILLS: (none)")

            # POV player deaths this round
            pov_deaths = [
                k for k in kills
                if k.get("round_num") == round_num
                and (k.get("victim") or "").lower() == pov_player.lower()
            ]
            if pov_deaths:
                for d in pov_deaths:
                    time_str = tick_to_video_time(d.get("tick", 0))
                    killer = d.get("attacker", "?")
                    weapon = d.get("weapon", "?")
                    round_lines.append(f"    DEATH @ {time_str}: killed by {killer} with {weapon}")
                    round_lines.append(f"      -> Tips after {time_str} are INVALID (spectating)")
            else:
                round_lines.append("    DEATH: (survived)")

            # POV player grenades this round
            pov_grenades = [
                g for g in grenades
                if g.get("round_num") == round_num
                and (g.get("thrower") or "").lower() == pov_player.lower()
            ]
            if pov_grenades:
                for g in pov_grenades:
                    time_str = tick_to_video_time(g.get("tick", 0))
                    nade_type = g.get("grenade_type", g.get("type", "?"))
                    round_lines.append(f"    GRENADE @ {time_str}: {nade_type}")
            else:
                round_lines.append("    GRENADES: (none)")

            # POV player damage dealt this round (summarized)
            pov_damage = [
                d for d in damages
                if d.get("round_num") == round_num
                and (d.get("attacker") or "").lower() == pov_player.lower()
            ]
            if pov_damage:
                total_dmg = sum(d.get("damage", 0) for d in pov_damage)
                victims = set(d.get("victim", "?") for d in pov_damage)
                round_lines.append(f"    DAMAGE: {total_dmg} total to {', '.join(victims)}")
            else:
                round_lines.append("    DAMAGE: (none)")

            # POV player bomb interactions this round
            pov_bomb = [
                b for b in bomb_events
                if b.get("round_num") == round_num
                and (b.get("player") or "").lower() == pov_player.lower()
            ]
            if pov_bomb:
                for b in pov_bomb:
                    time_str = tick_to_video_time(b.get("tick", 0))
                    event = b.get("event", "?")
                    site = b.get("site", "")
                    round_lines.append(f"    BOMB @ {time_str}: {event} {site}")

            lines.extend(round_lines)
            lines.append("")

        # Grenade usage summary (cross-reference for verifier)
        lines.extend([
            "-" * 60,
            "GRENADE USAGE SUMMARY (for verifying grenade tips):",
            "-" * 60,
        ])

        pov_grenades_all = [
            g for g in grenades
            if (g.get("thrower") or "").lower() == pov_player.lower()
        ]
        if pov_grenades_all:
            for g in sorted(pov_grenades_all, key=lambda x: x.get("tick", 0)):
                time_str = tick_to_video_time(g.get("tick", 0))
                round_num = g.get("round_num", "?")
                nade_type = g.get("grenade_type", g.get("type", "?"))
                lines.append(f"  R{round_num} @ {time_str}: {nade_type}")
        else:
            lines.append("  No grenades thrown by POV player")

        lines.append("")

        return lines

    def _build_pov_death_timeline(
        self,
        pov_player: str,
        kills: list,
        rounds: list,
        tickrate: int
    ) -> list:
        """
        Build a timeline of when the POV player died in each round.

        Returns list of dicts with:
        - round: round number
        - video_time: approximate video timestamp (e.g., "1:32")
        - killer: who killed the POV player
        - weapon: weapon used
        """
        if not kills or not rounds:
            return []

        # Use video_start_tick if available (for mid-match videos), otherwise use first round's freeze_end
        first_round_start = self.replay_data.get("video_start_tick")
        if first_round_start is None:
            first_round_start = rounds[0].get("freeze_end_tick") or rounds[0].get("start_tick") or 0

        # Find all deaths of POV player
        pov_deaths = []
        for kill in kills:
            if (kill.get("victim") or "").lower() == pov_player.lower():
                death_tick = kill.get("tick") or 0
                round_num = kill.get("round_num", 0)

                # Calculate video time
                video_seconds = (death_tick - first_round_start) / tickrate if first_round_start else 0
                video_seconds = max(0, video_seconds)  # Clamp to 0

                mins = int(video_seconds // 60)
                secs = int(video_seconds % 60)
                video_time = f"{mins}:{secs:02d}"

                pov_deaths.append({
                    "round": round_num,
                    "tick": death_tick,
                    "video_seconds": video_seconds,
                    "video_time": video_time,
                    "killer": kill.get("attacker", "Unknown"),
                    "weapon": kill.get("weapon", "Unknown"),
                })

        # Sort by round number
        pov_deaths.sort(key=lambda x: x["round"])

        return pov_deaths

    def _build_round_timeline(
        self,
        pov_player: str,
        kills: list,
        rounds: list,
        tickrate: int
    ) -> list:
        """
        Build a complete round timeline with start/end times and death info.

        Returns list of dicts with:
        - round: round number
        - start_video_time: when round starts (video timestamp)
        - end_video_time: when round ends (video timestamp)
        - death_video_time: when POV player died (or None if survived)
        - valid_range: time range where tips are valid
        """
        if not rounds:
            return []

        # Use video_start_tick if available (for mid-match videos), otherwise use first round's freeze_end
        first_round_start = self.replay_data.get("video_start_tick")
        if first_round_start is None:
            first_round_start = rounds[0].get("freeze_end_tick") or rounds[0].get("start_tick") or 0

        # Build death lookup
        death_by_round = {}
        for kill in kills:
            if (kill.get("victim") or "").lower() == pov_player.lower():
                round_num = kill.get("round_num", 0)
                death_tick = kill.get("tick", 0)
                death_by_round[round_num] = {
                    "tick": death_tick,
                    "killer": kill.get("attacker", "Unknown"),
                    "weapon": kill.get("weapon", "Unknown"),
                }

        # Build timeline
        timeline = []
        for rnd in rounds:
            round_num = rnd.get("round_num", 0)
            freeze_end = rnd.get("freeze_end_tick") or rnd.get("start_tick") or 0
            end_tick = rnd.get("end_tick") or 0

            # Calculate video times
            start_seconds = (freeze_end - first_round_start) / tickrate if first_round_start else 0
            start_seconds = max(0, start_seconds)
            end_seconds = (end_tick - first_round_start) / tickrate if first_round_start else 0
            end_seconds = max(0, end_seconds)

            start_time = f"{int(start_seconds // 60)}:{int(start_seconds % 60):02d}"
            end_time = f"{int(end_seconds // 60)}:{int(end_seconds % 60):02d}"

            # Check for death
            death_info = death_by_round.get(round_num)
            if death_info:
                death_seconds = (death_info["tick"] - first_round_start) / tickrate if first_round_start else 0
                death_seconds = max(0, death_seconds)
                death_time = f"{int(death_seconds // 60)}:{int(death_seconds % 60):02d}"
                valid_end = death_time
                status = f"DIED at {death_time} (killed by {death_info['killer']})"
            else:
                death_time = None
                death_seconds = None
                valid_end = end_time
                status = "SURVIVED"

            timeline.append({
                "round": round_num,
                "start_seconds": start_seconds,
                "start_time": start_time,
                "end_seconds": end_seconds,
                "end_time": end_time,
                "death_seconds": death_seconds,
                "death_time": death_time,
                "valid_range": f"{start_time} - {valid_end}",
                "status": status,
            })

        return timeline

    def _format_generic_replay(self) -> str:
        """Fallback generic format for unknown game types."""
        summary = self.replay_data.get("summary", {})
        players = summary.get("players", [])

        lines = [
            "=" * 50,
            "REPLAY DATA",
            "=" * 50,
            f"Map: {summary.get('map', 'Unknown')}",
            f"Duration: {summary.get('duration', 'Unknown')}",
            "",
            "PLAYERS:",
        ]

        for i, p in enumerate(players):
            player_num = i + 1
            winner_str = "[WINNER]" if p.get("winner") else ""
            name = p.get("name", "Unknown")
            lines.append(f"  Player {player_num}: {name} {winner_str}")

        lines.extend(["", "=" * 50])
        return "\n".join(lines)


def get_gemini_client() -> genai.Client:
    """Create a configured Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Try the multi-key env var
        api_keys_str = os.environ.get("GEMINI_API_KEYS", "")
        if api_keys_str:
            api_key = api_keys_str.split(",")[0].strip()

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY or GEMINI_API_KEYS environment variable required"
        )

    return genai.Client(api_key=api_key)


async def upload_video_to_gemini(client: genai.Client, video_path: str) -> Any:
    """
    Upload a video file to Gemini for analysis.

    Args:
        client: Gemini client
        video_path: Path to video file

    Returns:
        File object that can be passed to interactions
    """
    import asyncio

    logger.info(f"Uploading video to Gemini: {video_path}")

    # Run synchronous upload in thread pool to avoid blocking event loop
    def _sync_upload():
        with open(video_path, "rb") as f:
            return client.files.upload(
                file=f, config=types.UploadFileConfig(mime_type="video/mp4")
            )

    video_file = await asyncio.to_thread(_sync_upload)

    logger.info(f"Video uploaded: {video_file.name}, waiting for ACTIVE state...")

    # Wait for file to become ACTIVE
    max_wait = 300  # 5 minutes max
    waited = 0
    while waited < max_wait:
        # Run synchronous API call in thread pool
        file_info = await asyncio.to_thread(client.files.get, name=video_file.name)
        state = (
            file_info.state.name
            if hasattr(file_info.state, "name")
            else str(file_info.state)
        )

        if state == "ACTIVE":
            logger.info(f"Video file is ACTIVE: {video_file.name}")
            return file_info
        elif state == "FAILED":
            raise RuntimeError(f"Video file processing failed: {video_file.name}")

        logger.info(f"Video state: {state}, waiting...")
        await asyncio.sleep(5)
        waited += 5

    raise RuntimeError(f"Video file did not become ACTIVE within {max_wait}s")
