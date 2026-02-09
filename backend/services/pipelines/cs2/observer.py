"""
CS2 Observer Agent - Multi-Angle Analysis.

Analyzes CS2 gameplay video from three perspectives:
1. Exploitable Patterns (from opponent's POV)
2. Rank-Up Habits (what's holding you back)
3. Missed Adaptations (information -> reaction)

Generates 10-20 tips ordered by timestamp.
"""

import logging
from typing import Any, Optional

from services.agents.base import BaseAgent
from services.pipelines.cs2.contracts import (
    CS2ObserverOutput,
    CS2ObserverTip,
    Timestamp,
)

logger = logging.getLogger(__name__)


class CS2ObserverAgent(BaseAgent):
    """
    CS2 Observer: Round-based multi-angle gameplay analysis.

    Uses video: Yes
    Thinking level: HIGH (comprehensive analysis)
    """

    name = "cs2_observer"
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
        """Get the CS2-specific system prompt."""
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

### Angle 3: Information -> Reaction
Did they react to what they saw/heard?
- Sound cues ignored (footsteps, utility)
- Visual info not acted on
- Teammate callouts ignored

## OUTPUT FORMAT

Return at least 1 tip per round (ideally 2-3 per round), ordered by timestamp:
{
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

## TIP COUNT REQUIREMENTS - CRITICAL

You MUST generate a substantial number of tips. The player is paying for coaching feedback.

**MINIMUM REQUIREMENTS:**
- For a 7-minute video (4-5 rounds): Generate 8-15 tips
- For a 3-minute video (2-3 rounds): Generate 5-8 tips
- For a 15-minute video (10+ rounds): Generate 15-25 tips

**GUIDELINE: Approximately 2 tips per minute of gameplay footage.**

If you're about to return fewer than 8 tips for a multi-round video, GO BACK and look harder.

For EACH round, analyze:
1. Positioning mistakes (where they stood, peeked from)
2. Crosshair placement issues (head level, pre-aim)
3. Timing/pacing problems (too fast, too slow, predictable)
4. Utility usage (or lack thereof - smokes, flashes, mollies)
5. Information ignored (footsteps, callouts, visual cues)
6. Economy decisions (force buys, eco rounds, weapon choices)
7. Movement errors (running while shooting, not counter-strafing)
8. Trade potential (could teammate have traded, did they set up trades)
9. Reload habits (reloading at bad times)
10. Angle clearing (angles skipped, predictable clearing pattern)

**Every round has MULTIPLE learning moments. Find them all.**

## BEFORE YOU RESPOND - MANDATORY CHECKLIST

**TIP COUNT CHECK:**
[ ] Have I generated at least 8 tips? If not, go back and analyze more thoroughly
[ ] Did I find at least 1-2 tips per round? If not, look harder at each round

**For EACH tip you include:**
[ ] Find which round this timestamp falls into
[ ] Check: Is timestamp < death_seconds for that round? (If null, full round is valid)
[ ] The tip is about the POV player's OWN gameplay, not teammates
[ ] You can point to a SPECIFIC moment in the video
[ ] You are 100% certain you observed this - no guessing

**Quality over quantity, but quantity matters too.** The player deserves thorough feedback.
Aim for 10-15 verified tips. 3 tips is NOT enough for a multi-round video.

Return ONLY valid JSON."""

    def build_prompt(self, input_data: dict) -> str:
        """Build the observer prompt."""
        logger.info(f"[{self.name}] Building prompt for multi-angle analysis")

        # Format replay data for context
        replay_info = self.format_replay_data_for_prompt()

        # Build alive ranges from demo data (deterministic)
        alive_ranges_text = self._build_alive_ranges_text()

        prompt = f"""
## REPLAY DATA (for context)

{replay_info}

{alive_ranges_text}

## TASK

Watch this gameplay video and provide comprehensive feedback from THREE angles:

1. **Exploitable Patterns**: What would an opponent exploit?
2. **Rank-Up Habits**: What recurring habits are holding this player back?
3. **Information -> Reaction**: Did they react to what they saw/heard/scouted?

**CRITICAL: Generate 8-15 tips minimum.** The player needs detailed feedback to improve.
Aim for approximately 2 tips per minute of video. A 7-minute video should have 10-15 tips.
Analyze EVERY round thoroughly - each round typically has 2-3 improvement opportunities.

Order tips by timestamp. Each tip should be specific, actionable, and based on what you observe in the video.

Return your analysis as JSON.
"""
        logger.debug(f"[{self.name}] Prompt length: {len(prompt)} chars")
        return prompt

    def parse_response(self, response_text: str, input_data: dict) -> CS2ObserverOutput:
        """Parse the observer response."""
        logger.info(f"[{self.name}] Parsing observer response...")

        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[{self.name}] Could not parse JSON, returning empty output")
            return CS2ObserverOutput(tips=[], rounds_timeline=[])

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
                    CS2ObserverTip(
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

        # Note: rounds_timeline is now built from demo data (deterministic),
        # not from LLM output. See build_rounds_timeline_from_demo() in round_detector.py

        logger.info(f"[{self.name}] Found {len(tips)} tips")

        return CS2ObserverOutput(tips=tips, rounds_timeline=[])

    def _build_alive_ranges_text(self) -> str:
        """Build text describing valid analysis windows (when POV player is alive)."""
        # Get demo-built rounds timeline (set by pipeline)
        demo_rounds_timeline = self.replay_data.get("rounds_timeline_demo", [])

        if not demo_rounds_timeline:
            return ""

        lines = [
            "## VALID ANALYSIS WINDOWS - CRITICAL",
            "",
            "The POV player is ONLY visible during these time ranges.",
            "After death, the camera switches to spectating teammates - DO NOT analyze that footage.",
            "",
        ]

        for r in demo_rounds_timeline:
            round_num = r.get("round", 0)
            start_time = r.get("start_time", "0:00")
            end_time = r.get("end_time", "0:00")
            death_time = r.get("death_time")
            death_seconds = r.get("death_seconds")

            if death_time:
                # Player died - valid window ends at death
                lines.append(
                    f"Round {round_num}: {start_time} - {death_time} (DIED - stop analyzing after {death_time})"
                )
            else:
                # Player survived - valid window is full round
                lines.append(f"Round {round_num}: {start_time} - {end_time} (SURVIVED)")

        lines.extend([
            "",
            "⚠️ MANDATORY: Check EVERY tip timestamp against these windows.",
            "Tips after death time will be REJECTED by the validator.",
        ])

        return "\n".join(lines)
