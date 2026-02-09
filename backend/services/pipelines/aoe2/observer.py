"""
AoE2 Observer Agent - Multi-Angle Analysis.

Analyzes AoE2 gameplay video from three perspectives:
1. Exploitable Patterns (from opponent's POV)
2. Rank-Up Habits (what's holding you back)
3. Missed Adaptations (scouting -> reaction)

Generates 10-20 tips ordered by timestamp.
"""

import logging
from typing import Any, Optional

from services.agents.base import BaseAgent
from services.pipelines.aoe2.contracts import (
    AoE2ObserverOutput,
    AoE2ObserverTip,
    Timestamp,
)

logger = logging.getLogger(__name__)


# Import knowledge base - will be refactored to services/knowledge/aoe2.py later
try:
    from services.aoe2_knowledge import AOE2_KNOWLEDGE
except ImportError:
    from services.knowledge.aoe2 import AOE2_KNOWLEDGE


class AoE2ObserverAgent(BaseAgent):
    """
    AoE2 Observer: Phase-based multi-angle gameplay analysis.

    Uses video: Yes
    Thinking level: HIGH (comprehensive analysis)

    Key differences from CS2:
    - No round-based structure (continuous gameplay)
    - Game time vs video time conversion (1.5x speed)
    - Phase-based analysis (Dark/Feudal/Castle/Imperial)
    """

    name = "aoe2_observer"
    uses_video = True
    thinking_level = "high"
    include_thoughts = False

    # Structured output schema for native JSON enforcement
    response_schema = {
        "type": "object",
        "properties": {
            "tips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "timestamp": {
                            "type": "object",
                            "properties": {
                                "video_seconds": {"type": "integer"},
                                "display": {"type": "string"},
                                "game_time": {"type": "string"},
                            },
                            "required": ["video_seconds", "display"],
                        },
                        "category": {"type": "string"},
                        "severity": {"type": "string"},
                        "observation": {"type": "string"},
                        "why_it_matters": {"type": "string"},
                        "fix": {"type": "string"},
                        "reasoning": {"type": "string"},
                        "recurring_timestamps": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "id", "timestamp", "category", "severity",
                        "observation", "why_it_matters", "fix",
                    ],
                },
            },
        },
        "required": ["tips"],
    }

    def get_system_prompt(self) -> str:
        """Get the AoE2-specific system prompt."""
        return f"""You are an expert Age of Empires II: Definitive Edition coach with 2000+ ELO.
You are analyzing gameplay footage to provide specific, actionable coaching tips.

## VIDEO HUD GUIDE

The AoE2 DE interface shows critical information:

**TOP LEFT:**
- Resources in order: Wood, Food, Gold, Stone (with current amounts)
- Population: Current / Maximum (e.g., "15/26" means 15 pop out of 26 max)

**TOP CENTER:**
- Current Age text (e.g., "Dark Age", "Feudal Age", "Castle Age", "Imperial Age")
- In replays: Game time clock may appear here or near the age indicator

**TOP RIGHT:**
- Idle villager button (click to cycle through idle villagers)
- Player scores showing player names and their scores (e.g., "PlayerName: 561/561")

**BOTTOM LEFT:**
- Selected unit/building info panel
- Shows building name, stats, and production queue (e.g., "Town Center" with "Creating 4% Villager")

**BOTTOM RIGHT:**
- Minimap showing terrain, units, and buildings
- POV player's color is visible here
- Enemy units appear as different colored dots

**LEFT SIDE (below resources):**
- Event log showing recent events (e.g., "--House Built--", "--Villager Created--")

Use these HUD elements to verify your observations against what you SEE in the video.

## CRITICAL RULES

### Rule 1: ONLY analyze the POV player
- The video shows ONE player's perspective
- Only comment on THIS player's actions and decisions
- Do NOT critique the opponent's play
- If you can't see an action happen, don't assume it happened

### Rule 2: VIDEO is the source of truth
- If analyzing idle TC, you must SEE the TC not producing
- If analyzing floating resources, you must SEE high resource counts in HUD
- Don't assume based on typical patterns - VERIFY in the video

### Rule 3: Cross-reference with REPLAY DATA
- The REPLAY DATA section contains parsed information from the game file
- Use it to verify building counts, research timings, age-up times
- If video shows 2 Archery Ranges but replay data shows 1, trust the replay data

### Rule 4: Account for game speed
- Game runs at 1.5x speed on Normal/Standard
- Game time 9:00 = Video/Real time 6:00
- Always output VIDEO timestamps, not game time

## HOW TO IDENTIFY COMMON GAME STATES

**Idle Town Center:**
- No villager walking out of TC
- No progress bar on TC
- Idle villager counter may be increasing

**Getting Housed:**
- Population shows X/X (e.g., "50/50")
- Production buildings show queued units but no progress
- Player scrambles to build houses

**Floating Resources:**
- Resource counters show 500+ of any resource
- Player has unspent resources while not being attacked
- NOT floating if: saving for age-up, saving for Castle drop, intentional bank

**Idle Villagers:**
- Villagers standing still not gathering
- Idle villager counter shows > 0
- Common after: building completion, depleted resource, attacked and fled

**Age Transition:**
- TC shows age-up progress bar
- "Advancing to X Age" visible
- Resources drop significantly when clicked

## ANALYSIS ANGLES

Analyze from THREE perspectives:

### Angle 1: Exploitable Patterns
What would an opponent exploit about this player?
- Predictable build order variations
- Wall gaps or defensive weaknesses
- Resource gathering patterns
- Army composition predictability

### Angle 2: Rank-Up Habits
What habits cost them games?
- Idle TC time
- Resource floating
- Late age-up timings
- Poor unit control

### Angle 3: Scouting -> Reaction
Did they react to what they scouted?
- Opponent's strategy visible but ignored
- Counter units not built
- Forward buildings not addressed

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
- Tip: "While deer luring is efficient, you missed scouting the enemy Barracks. Earlier scouting would have revealed the M@A rush."

## GROUPING RECURRING PATTERNS

When you see the SAME mistake happen multiple times, CONSOLIDATE into ONE tip with recurring_timestamps:

GOOD (consolidated):
{{
  "observation": "Town Center idle for 20+ seconds multiple times in Dark Age",
  "recurring_timestamps": ["1:30", "3:45", "5:10", "7:20"],
  "fix": "Queue 2-3 villagers at a time, check TC after every action"
}}

BAD (don't create separate tips for the same issue):
- Tip 1: "At 1:30 your TC was idle"
- Tip 2: "At 3:45 your TC was idle"
- Tip 3: "At 5:10 your TC was idle"

The recurring_timestamps field shows this is a PATTERN, not a one-time mistake.
Patterns are more valuable feedback than isolated incidents.

## OUTPUT FORMAT

Return as many tips as you find (aim for 10-20), ordered by timestamp:
{{
  "tips": [
    {{
      "id": "tip_001",
      "timestamp": {{"video_seconds": 180, "display": "3:00"}},
      "category": "rank_up_habit",
      "severity": "critical",
      "observation": "Town Center idle for 30+ seconds multiple times in Dark Age",
      "why_it_matters": "You're 3-4 villagers behind where you should be by Feudal Age",
      "fix": "Queue 2-3 villagers at a time, check TC every time you build something",
      "reasoning": "Observed TC idle at 1:30-2:00, 3:45-4:20, and 5:10-5:45",
      "recurring_timestamps": ["1:30", "3:45", "5:10"]
    }},
    {{
      "id": "tip_002",
      "timestamp": {{"video_seconds": 300, "display": "5:00"}},
      "category": "exploitable_pattern",
      "severity": "important",
      "observation": "Wall placement leaves gold vulnerable to archer harassment",
      "why_it_matters": "Enemy archers can kill villagers on gold from outside the wall",
      "fix": "Wall further out or use houses to protect the gold line",
      "reasoning": "Wall at 5:00 is only 2 tiles from gold mining camp"
    }},
    {{
      "id": "tip_003",
      "timestamp": {{"video_seconds": 600, "display": "10:00"}},
      "category": "missed_adaptation",
      "severity": "critical",
      "observation": "Scouted 2 archery ranges but continued pure knight production",
      "why_it_matters": "Knights get destroyed by mass archers without support",
      "fix": "Add skirmishers or scout cavalry to counter archers",
      "reasoning": "Scout passed 2 archery ranges at 9:50, player queued more knights at 10:10"
    }}
  ]
}}

## CATEGORIES

Use these categories:
- exploitable_pattern: Something an opponent could exploit
- rank_up_habit: A recurring habit holding the player back
- missed_adaptation: Failed to react to scouted information
- economy: Economy/resource management issue
- military: Army composition or control issue
- scouting: Scouting execution issue
- macro: General macro issue (TC, production, etc.)

## SEVERITY LEVELS

- critical: Game-changing issue that must be fixed first
- important: Significant improvement opportunity
- minor: Nice to fix but not urgent

## TIP COUNT REQUIREMENTS - CRITICAL

You MUST generate a substantial number of tips. The player is paying for coaching feedback.

**MINIMUM REQUIREMENTS:**
- For a 10-minute video (Dark to early Feudal): Generate 8-12 tips
- For a 20-minute video (through Castle Age): Generate 12-18 tips
- For a 30+ minute video (full game): Generate 18-25 tips

**GUIDELINE: Approximately 1 tip per minute of gameplay footage.**

If you're about to return fewer than 8 tips, GO BACK and look harder.

For EACH game phase, analyze:

**Dark Age (0-10 min game time):**
1. Idle TC time (the #1 issue for most players)
2. Sheep management (killing multiple sheep, letting them decay)
3. Boar luring (late lures, villager deaths)
4. Scout usage (idle scout, missing sheep/boar/enemy)
5. Build order execution (wrong villager assignments)
6. Getting housed (population cap hit)

**Feudal Age (10-20 min game time):**
7. Resource floating (500+ unspent resources)
8. Late age-up timing (compare to standard benchmarks)
9. Military production (idle production buildings)
10. Scouting reaction (seeing enemy strategy but not adapting)
11. Walling (gaps, late walls, no walls on open maps)
12. Upgrade timing (Blacksmith, eco upgrades)

**Castle Age and beyond:**
13. TC boom timing (when to add TCs)
14. Army composition (countered by enemy units)
15. Map control (relics, neutral golds, map presence)
16. Siege usage (when to add siege)
17. Trading (late trade setup)

**Every game has MULTIPLE learning moments in each phase. Find them all.**

## BEFORE YOU RESPOND - MANDATORY CHECKLIST

**TIP COUNT CHECK:**
[ ] Have I generated at least 8 tips? If not, go back and analyze more thoroughly
[ ] Did I cover multiple game phases? If not, look at each phase carefully

**For EACH tip you include:**
[ ] The tip is about the POV player's OWN gameplay, not opponent
[ ] You can point to a SPECIFIC moment or pattern in the video
[ ] You have VERIFIED this in the video - no guessing
[ ] The timestamp is in VIDEO time (not game time)
[ ] If it's a recurring issue, you've consolidated into one tip with recurring_timestamps

**Quality over quantity, but quantity matters too.** The player deserves thorough feedback.
Aim for 10-15 verified tips. 3 tips is NOT enough for a full game.

## AOE2 STRATEGIC KNOWLEDGE

{AOE2_KNOWLEDGE}

Return ONLY valid JSON."""

    def build_prompt(self, input_data: dict) -> str:
        """Build the observer prompt."""
        logger.info(f"[{self.name}] Building prompt for multi-angle analysis")

        # Format replay data for context
        replay_info = self.format_replay_data_for_prompt()

        prompt = f"""
## REPLAY DATA (THIS IS GROUND TRUTH - DO NOT CONTRADICT)

{replay_info}

## TASK

Watch this Age of Empires 2 gameplay video and provide comprehensive feedback from THREE angles:

1. **Exploitable Patterns**: What would an opponent exploit?
2. **Rank-Up Habits**: What recurring habits are holding this player back?
3. **Scouting -> Reaction**: Did they react to what they scouted?

## CRITICAL REMINDERS

**TIMESTAMPS:**
- Use VIDEO TIME (real time), NOT game time
- Divide game time by 1.5 to get video time
- Example: Game time 6:00 = Video time 4:00

**VERIFICATION:**
- Only include tips you can VERIFY in the video
- Cross-check building counts, research, and timings against REPLAY DATA above
- If REPLAY DATA contradicts what you think you see, trust REPLAY DATA

**OUTPUT:**
- Order tips by timestamp (chronological)
- Consolidate recurring patterns into ONE tip with recurring_timestamps
- Each tip must be specific and actionable

**CRITICAL: Generate 8-15 tips minimum.** The player needs detailed feedback to improve.
Aim for approximately 1 tip per minute of video. A 20-minute video should have 15-20 tips.
Analyze EVERY game phase thoroughly - Dark Age, Feudal, Castle each have multiple improvement opportunities.

Return your analysis as JSON.
"""
        logger.debug(f"[{self.name}] Prompt length: {len(prompt)} chars")
        return prompt

    def parse_response(self, response_text: str, input_data: dict) -> AoE2ObserverOutput:
        """Parse the observer response."""
        logger.info(f"[{self.name}] Parsing observer response...")

        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[{self.name}] Could not parse JSON, returning empty output")
            return AoE2ObserverOutput(tips=[])

        # Parse tips
        tips = []
        for tip in data.get("tips", []):
            try:
                ts = tip.get("timestamp")
                timestamp = None
                if ts:
                    timestamp = Timestamp(
                        video_seconds=ts.get("video_seconds", 0),
                        display=ts.get("display", "0:00"),
                        game_time=ts.get("game_time"),
                    )

                tips.append(
                    AoE2ObserverTip(
                        id=tip.get("id", f"tip_{len(tips)+1:03d}"),
                        timestamp=timestamp,
                        category=tip.get("category", "general"),
                        severity=tip.get("severity", "important"),
                        observation=tip.get("observation", ""),
                        why_it_matters=tip.get("why_it_matters", ""),
                        fix=tip.get("fix", ""),
                        reasoning=tip.get("reasoning"),
                        recurring_timestamps=tip.get("recurring_timestamps"),
                    )
                )
                logger.info(f"[{self.name}] Tip: {tip.get('observation', '')[:100]}...")
            except Exception as e:
                logger.warning(f"[{self.name}] Error parsing tip: {e}")

        # Sort tips by timestamp
        tips.sort(key=lambda t: t.timestamp.video_seconds if t.timestamp else 0)

        logger.info(f"[{self.name}] Found {len(tips)} tips")

        return AoE2ObserverOutput(tips=tips)
