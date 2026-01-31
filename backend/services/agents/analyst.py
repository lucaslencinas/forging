"""
Analyst Agent - Combined Multi-Angle Analysis

Single agent that combines all three analysis perspectives:
1. Exploitable Patterns (from opponent's POV)
2. Rank-Up Habits (what's holding you back)
3. Missed Adaptations (information → reaction)

Generates up to 20 tips ordered by timestamp.
"""

import logging
from typing import Any

from .base import BaseAgent
from .contracts import (
    AnalystOutput,
    AnalystTip,
    Timestamp,
)

logger = logging.getLogger(__name__)


class ObserverAgent(BaseAgent):
    """
    Observer: Combined multi-angle gameplay analysis.

    Uses video: Yes
    Thinking level: HIGH (comprehensive analysis)
    """

    name = "observer"
    uses_video = True
    thinking_level = "high"
    include_thoughts = False

    def get_system_prompt(self) -> str:
        """Get the system prompt based on game type."""
        if self.game_type == "cs2":
            return self._get_cs2_system_prompt()
        else:
            return self._get_aoe2_system_prompt()

    def _get_cs2_system_prompt(self) -> str:
        return """You are a CS2 gameplay analyst. Watch this video and provide comprehensive feedback.

## VIDEO HUD GUIDE

On the LEFT side of the video, you can see an overlay with:
1. A MINIMAP showing the current map layout
2. Below the minimap: the CURRENT LOCATION of the POV player (e.g., "Long Doors", "A Site", "Mid", "T Spawn")
3. The POV player's NAME is shown in the HUD

Use the location text to accurately describe WHERE the player is at any moment.

## CRITICAL RULES

### Rule 1: ONLY analyze while the player is ALIVE
- Once the player dies in a round, STOP analyzing until next round
- Do NOT comment on teammates' plays
- Do NOT critique what happens during spectating
- The REPLAY DATA section below tells you EXACTLY when the POV player died in each round - USE IT!

### Rule 2: VIDEO is the source of truth
- If analyzing flash reactions, CHECK if the screen actually went white
- A flashbang thrown nearby does NOT mean they were flashed (walls block flashes)
- Only critique flash reactions if you can SEE the screen go white

### Rule 3: Verify against REPLAY DATA
The REPLAY DATA section contains the POV player's death timestamps extracted from the demo file.
Cross-reference your observations with these timestamps:
- If you're about to make a tip at timestamp X, check if the player was already dead
- The death timestamps in REPLAY DATA are authoritative

## HOW TO KNOW WHEN THE PLAYER DIES

In CS2, when the POV player dies:
- The screen shows a death animation (falling/fading)
- The view switches to spectating a teammate
- The player name in the corner changes to a teammate's name
- A "You were killed by [enemy]" message may appear

Once you see ANY of these, STOP analyzing that round.

## ANALYSIS ANGLES

Analyze from THREE perspectives:

### Angle 1: Exploitable Patterns
What would an enemy exploit about this player?
- Predictable peek timings/positions
- Corners never checked
- Utility timing patterns
- Same angles held every round

### Angle 2: Rank-Up Habits
What habits cost them rounds?
- Recurring patterns, not one-time mistakes
- Crosshair placement issues
- Movement/positioning habits
- Economy mistakes

### Angle 3: Information → Reaction
Did they react to what they saw/heard?
- Sound cues ignored (footsteps, utility)
- Visual info not acted on
- Teammate callouts ignored

## OUTPUT FORMAT

Return as many tips as you find (aim for 10-20), ordered by timestamp:
{
  "rounds_timeline": [
    {"round": 1, "start_seconds": 5, "death_seconds": 32, "end_seconds": 45},
    {"round": 2, "start_seconds": 50, "death_seconds": null, "end_seconds": 110}
  ],
  "tips": [
    {
      "id": "tip_001",
      "timestamp": {"video_seconds": 45, "display": "0:45"},
      "category": "exploitable_pattern",
      "severity": "critical",
      "observation": "Player always peeks mid doors same timing",
      "why_it_matters": "Predictable timing = free kills for enemies",
      "fix": "Vary your timing - sometimes early, sometimes late, sometimes don't peek",
      "reasoning": "Observed in rounds 2, 5, and 8 - always peeked 3 seconds after smoke faded",
      "recurring_timestamps": ["0:45", "2:15", "4:30"]
    },
    {
      "id": "tip_002",
      "timestamp": {"video_seconds": 120, "display": "2:00"},
      "category": "rank_up_habit",
      "severity": "critical",
      "observation": "Crosshair at chest level when holding angles",
      "why_it_matters": "You lose aim duels because you have to flick UP to the head",
      "fix": "Keep crosshair at head level - use door frames as reference",
      "reasoning": "Crosshair consistently below head level in rounds 1, 3, 5, and 7",
      "recurring_timestamps": ["0:30", "2:00", "3:45", "5:10"]
    },
    {
      "id": "tip_003",
      "timestamp": {"video_seconds": 180, "display": "3:00"},
      "category": "missed_adaptation",
      "severity": "important",
      "observation": "Heard 3+ footsteps going A but continued B push alone",
      "why_it_matters": "Information was available but ignored",
      "fix": "When you hear multiple enemies in one location, adjust your approach",
      "reasoning": "Audio clearly picked up footsteps at 2:58, player continued B push at 3:00"
    }
  ]
}

## GROUPING RECURRING PATTERNS

When you see the SAME mistake happen multiple times, CONSOLIDATE into ONE tip with recurring_timestamps:

GOOD (consolidated):
{
  "observation": "You reload immediately after kills even with 15+ bullets remaining",
  "recurring_timestamps": ["1:23", "2:45", "4:12", "5:38"],
  "fix": "Only reload if below 10 bullets OR when safe behind cover"
}

BAD (don't create separate tips for the same issue):
- Tip 1: "At 1:23 you reloaded too early"
- Tip 2: "At 2:45 you reloaded too early"
- Tip 3: "At 4:12 you reloaded too early"

The recurring_timestamps field shows this is a PATTERN, not a one-time mistake.
Patterns are more valuable feedback than isolated incidents.

## CATEGORIES

Use these categories:
- exploitable_pattern: Something an opponent could exploit
- rank_up_habit: A recurring habit holding the player back
- missed_adaptation: Failed to react to information
- positioning: General positioning issue
- utility: Utility usage issue
- economy: Economy/buy decision issue
- aim: Aim/crosshair issue

## SEVERITY LEVELS

- critical: Game-changing issue that must be fixed first
- important: Significant improvement opportunity
- minor: Nice to fix but not urgent

## BEFORE YOU RESPOND - MANDATORY CHECKLIST

For EACH tip you include:
[ ] Find which round this timestamp falls into
[ ] Check: Is timestamp < death_seconds for that round? (If null, full round is valid)
[ ] The tip is about the POV player's OWN gameplay, not teammates
[ ] You can point to a SPECIFIC moment in the video
[ ] You are 100% certain you observed this - no guessing

**It's better to return 10 verified tips than 20 uncertain ones.**

Return ONLY valid JSON."""

    def _get_aoe2_system_prompt(self) -> str:
        return """You are an AoE2 gameplay analyst. Watch this video and provide comprehensive feedback.

## CRITICAL: PLAYER IDENTIFICATION

**BEFORE analyzing anything, you MUST identify which player's POV the video shows:**

The video shows one player's perspective. To identify them:
1. Look at the minimap orientation - your base is typically at the bottom
2. Note the color of YOUR Town Center and villagers in the video
3. Match that color to the player list in the REPLAY DATA section
4. The HUD shows YOUR resources and population
5. Actions you see being performed belong to the POV player

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

### Angle 3: Scouting → Reaction
Did they react to what they scouted?
- Opponent's strategy visible but ignored
- Counter units not built
- Forward buildings not addressed

## OUTPUT FORMAT

Return as many tips as you find (aim for 10-20), ordered by timestamp:
{
  "tips": [
    {
      "id": "tip_001",
      "timestamp": {"video_seconds": 180, "display": "3:00"},
      "category": "rank_up_habit",
      "severity": "critical",
      "observation": "Town Center idle for 30+ seconds multiple times in Dark Age",
      "why_it_matters": "You're 3-4 villagers behind where you should be by Feudal Age",
      "fix": "Queue 2-3 villagers at a time, check TC every time you build something",
      "reasoning": "Observed TC idle at 1:30-2:00, 3:45-4:20, and 5:10-5:45"
    },
    {
      "id": "tip_002",
      "timestamp": {"video_seconds": 300, "display": "5:00"},
      "category": "exploitable_pattern",
      "severity": "important",
      "observation": "Wall placement leaves gold vulnerable to archer harassment",
      "why_it_matters": "Enemy archers can kill villagers on gold from outside the wall",
      "fix": "Wall further out or use houses to protect the gold line",
      "reasoning": "Wall at 5:00 is only 2 tiles from gold mining camp"
    },
    {
      "id": "tip_003",
      "timestamp": {"video_seconds": 600, "display": "10:00"},
      "category": "missed_adaptation",
      "severity": "critical",
      "observation": "Scouted 2 archery ranges but continued pure knight production",
      "why_it_matters": "Knights get destroyed by mass archers without support",
      "fix": "Add skirmishers or scout cavalry to counter archers",
      "reasoning": "Scout passed 2 archery ranges at 9:50, player queued more knights at 10:10"
    }
  ]
}

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

## IMPORTANT NOTES

- Use VIDEO TIME for timestamps, not game time
- Order tips by timestamp (chronological order)
- Focus on patterns (recurring issues), not one-time mistakes
- Include your reasoning for EACH tip
- Be specific about what you saw

**It's better to return 10 verified tips than 20 uncertain ones.**

Return ONLY valid JSON."""

    def build_prompt(self, input_data: dict) -> str:
        """Build the analyst prompt."""
        logger.info(f"[{self.name}] Building prompt for multi-angle analysis")

        # Format replay data for context
        replay_info = self.format_replay_data_for_prompt()

        prompt = f"""
## REPLAY DATA (for context)

{replay_info}

## TASK

Watch this gameplay video and provide comprehensive feedback from THREE angles:

1. **Exploitable Patterns**: What would an opponent exploit?
2. **Rank-Up Habits**: What recurring habits are holding this player back?
3. **Information → Reaction**: Did they react to what they saw/heard/scouted?

Generate as many tips as you find (aim for 10-20), ordered by timestamp.
Each tip should be specific, actionable, and based on what you observe in the video.

Return your analysis as JSON.
"""
        logger.debug(f"[{self.name}] Prompt length: {len(prompt)} chars")
        return prompt

    def parse_response(self, response_text: str, input_data: dict) -> AnalystOutput:
        """Parse the analyst response."""
        logger.info(f"[{self.name}] Parsing analyst response...")

        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[{self.name}] Could not parse JSON, returning empty output")
            return AnalystOutput(tips=[])

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
                    )

                tips.append(
                    AnalystTip(
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
                logger.info(
                    f"[{self.name}] Tip: {tip.get('observation', '')[:100]}..."
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Error parsing tip: {e}")

        # Sort tips by timestamp
        tips.sort(key=lambda t: t.timestamp.video_seconds if t.timestamp else 0)

        # Extract rounds timeline if present
        rounds_timeline = data.get("rounds_timeline") or data.get("rounds")

        logger.info(f"[{self.name}] Found {len(tips)} tips")

        return AnalystOutput(tips=tips, rounds_timeline=rounds_timeline)
