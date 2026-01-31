"""
Verifier Agent - 2-Step Verification with Confidence Scoring

Verifies tips from the Analyst agent:
1. Video Cross-Check: Go to timestamp, watch 5s before and after
2. Demo File Cross-Check: Verify action was by POV player at claimed timestamp

Assigns confidence scores 1-10:
- 9-10: Clearly visible in video AND confirmed in demo data
- 8: Visible in video, demo data supports it
- 5-7: Action happened but timestamp may be off OR by different player
- 1-4: Hallucination - action didn't happen or completely wrong

Only tips with confidence >= 8 are returned.
"""

import logging
import os
from typing import Any, Optional

from .base import BaseAgent
from .contracts import (
    AnalystOutput,
    ProducerOutput,
    RemovedTip,
    Timestamp,
    VerifiedTip,
    VerifierOutput,
)

logger = logging.getLogger(__name__)


class ValidatorAgent(BaseAgent):
    """
    Validator: 2-step verification with confidence scoring.

    Uses video: Yes (for verification)
    Thinking level: HIGH (careful verification)
    """

    name = "validator"
    uses_video = True
    thinking_level = "high"
    include_thoughts = False

    def get_system_prompt(self) -> str:
        """Not used - Verifier uses custom verify method."""
        return ""

    def build_prompt(self, input_data: dict) -> str:
        """Not used - Verifier uses custom verify method."""
        return ""

    def parse_response(self, response_text: str, input_data: dict) -> Any:
        """Not used - Verifier uses custom verify method."""
        return None

    async def verify(self, analyst_output: AnalystOutput) -> ProducerOutput:
        """
        Verify tips from the Analyst and return final output.

        Args:
            analyst_output: Output from the Analyst agent

        Returns:
            ProducerOutput with verified tips and summary
        """
        logger.info(f"[{self.name}] Starting verification of {len(analyst_output.tips)} tips")

        # Build verification prompt
        system_prompt = self._get_verification_system_prompt()
        user_prompt = self._build_verification_prompt(analyst_output)

        logger.info(f"[{self.name}] System prompt: {len(system_prompt)} chars")
        logger.info(f"[{self.name}] User prompt: {len(user_prompt)} chars")

        # Build content with video
        if self.video_file:
            input_content = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "video",
                    "uri": self.video_file.uri,
                    "mime_type": "video/mp4",
                },
            ]
            logger.info(f"[{self.name}] Including video: {self.video_file.uri}")
        else:
            input_content = [{"type": "text", "text": user_prompt}]

        # Call the model
        interaction = self.client.interactions.create(
            model=os.getenv("TURTLE_MODEL", "gemini-3-pro-preview"),
            input=input_content,
            system_instruction=system_prompt,
            generation_config={
                "thinking_level": self.thinking_level,
            },
        )

        # Extract response
        response_text = ""
        if hasattr(interaction, "outputs") and interaction.outputs:
            last_output = interaction.outputs[-1]
            if hasattr(last_output, "text"):
                response_text = last_output.text
            elif hasattr(last_output, "parts"):
                for part in last_output.parts:
                    if hasattr(part, "text"):
                        response_text += part.text

        logger.info(f"[{self.name}] Verification response: {len(response_text)} chars")

        # Parse the response
        verifier_output = self._parse_verification_response(response_text)

        # Build final output
        final_output = ProducerOutput(
            tips=verifier_output.verified_tips,
            summary_text=verifier_output.summary_text,
            pipeline_metadata={
                "analyst_tips_count": len(analyst_output.tips),
                "verified_tips_count": len(verifier_output.verified_tips),
                "removed_tips_count": len(verifier_output.removed_tips),
                "removed_tips": [t.model_dump() for t in verifier_output.removed_tips],
            },
        )

        logger.info(
            f"[{self.name}] Verification complete: "
            f"{len(verifier_output.verified_tips)} verified, "
            f"{len(verifier_output.removed_tips)} removed"
        )

        return final_output

    def _get_verification_system_prompt(self) -> str:
        """System prompt for verification."""
        base_prompt = """You are a Verifier agent. Your job is to cross-check tips against video evidence.

## VIDEO HUD GUIDE

On the LEFT side of the video, you can see an overlay with:
1. A MINIMAP showing the current map layout
2. Below the minimap: the CURRENT LOCATION of the POV player (e.g., "Long Doors", "A Site", "Mid", "T Spawn")
3. The POV player's NAME is shown in the HUD

Use the location text to verify if the tip's location description is accurate.

## YOUR MISSION

For EACH tip from the Analyst:
1. Go to the claimed timestamp in the video
2. Watch 5 seconds BEFORE and 5 seconds AFTER the timestamp
3. Verify the described event actually happened
4. Check the LOCATION text in the HUD matches the tip's description
5. Assign a confidence score (1-10)
6. Keep tips with confidence >= 8, remove the rest

## VERIFICATION PROCESS

### Step 1: Video Cross-Check
For each tip:
- Navigate to the timestamp
- Watch the 10-second window (5s before, 5s after)
- Did the described event happen?
- Is the timestamp accurate?
- Does the LOCATION shown in the HUD match the tip's location?

### Step 2: POV Player Verification
- Is this about the POV player's actions (not teammates)?
- Was the player ALIVE at this timestamp? (Check the DEATH TIMELINE in REPLAY DATA)
- Is the described action visible in the video?

## CONFIDENCE SCORING

Assign a score 1-10 for each tip:

**9-10: HIGH CONFIDENCE**
- Clearly visible in video
- Timestamp is accurate (within 5 seconds)
- Event is exactly as described
- About the POV player's own actions

**8: GOOD CONFIDENCE**
- Visible in video
- Timestamp is close (within 10 seconds)
- Event mostly matches description
- About the POV player

**5-7: MEDIUM CONFIDENCE (REMOVE)**
- Action happened but timestamp is off by >15 seconds
- OR action was by a different player
- OR description doesn't quite match what you see

**1-4: LOW CONFIDENCE (REMOVE - HALLUCINATION)**
- Event didn't happen at all
- Complete mismatch with video
- Player was dead/spectating at this time
- Describes teammate actions, not POV player

## RULES FOR REMOVAL

REMOVE a tip if:
- Confidence < 8
- Player was dead at the timestamp (check rounds timeline)
- Tip is about a teammate's actions
- Event is not visible in the 10-second window
- Description contradicts what you see in video

DO NOT add new tips - only verify existing ones.

## OUTPUT FORMAT

Return JSON:
{
  "verified_tips": [
    {
      "id": "tip_001",
      "timestamp": {"video_seconds": 45, "display": "0:45"},
      "category": "exploitable_pattern",
      "severity": "critical",
      "tip_text": "You always peek mid doors with the same timing - enemies can easily pre-aim",
      "source": "analyst",
      "confidence": 9,
      "verification_notes": "Confirmed at 0:43-0:47, player peeked mid doors same way as rounds 2, 5"
    }
  ],
  "removed_tips": [
    {
      "id": "tip_005",
      "reason": "Action was by teammate, not POV player",
      "confidence": 3
    },
    {
      "id": "tip_008",
      "reason": "Player was dead at this timestamp (spectating)",
      "confidence": 2
    }
  ],
  "summary_text": "100-300 char TTS summary of key improvements..."
}

## TIP TEXT FORMATTING

When creating tip_text from the Analyst's observation + fix:
- Be concise but actionable
- Format: "Issue observed. How to fix."
- Example: "You always peek mid doors with the same timing. Vary your approach - sometimes early, sometimes late."

## SUMMARY GUIDELINES

Write a 100-300 character summary that:
- Will be read aloud via TTS
- Summarizes the 2-3 most important improvements
- Is conversational and encouraging but honest
- Focuses on what to practice

Example summaries:
- "Focus on crosshair placement and timing variation. You're getting picked at predictable angles - mix it up and you'll win more duels."
- "Your biggest issue is idle TC time. Keep villagers queued and you'll hit Feudal faster, which fixes most of your problems."

Return ONLY valid JSON."""

        # Add game-specific CS2 rules
        if self.game_type == "cs2":
            base_prompt += """

## CS2-SPECIFIC RULES

### MANDATORY CROSS-CHECKS (Do ALL of these for EVERY tip)

For EACH tip, you MUST verify against the REPLAY DATA:

**1. DEATH CHECK:**
   - Look up which round this timestamp falls into (use ROUND TIMELINE)
   - If tip_timestamp > death_time for that round → REJECT (player was spectating)
   - If death_time is null for that round → player survived, full round is valid

**2. ACTION OWNERSHIP:**
   - Look up in POV PLAYER ACTIONS section
   - If tip says "you threw a flashbang" → VERIFY the grenade appears in POV's grenades list
   - If tip says "you got a kill" → VERIFY in POV's kills list
   - If the action is NOT in POV's actions → REJECT (was teammate/enemy action)

**3. GRENADE TYPE VERIFICATION:**
   - If tip mentions a grenade, cross-check GRENADE USAGE SUMMARY
   - flashbang ≠ smokegrenade ≠ molotov ≠ hegrenade
   - If type mismatch → REJECT or correct the grenade type

**4. GAME STATE VERIFICATION:**
   - If tip references bomb status (planted/defused):
   - Check ROUND RESULTS for bomb_planted (true/false) and bomb_site
   - If tip says "bomb planted B" but data shows no plant or wrong site → REJECT

**5. VISUAL VERIFICATION:**
   - If tip says "you were flashed" → screen MUST go white in video
   - If tip says "you crouched" → viewpoint MUST lower in video
   - Don't trust assumptions; verify what you actually SEE

### HALLUCINATION RED FLAGS - AUTO-REJECT

These are common fabrications. Be VERY skeptical if you see these:

- "You stood still while flashed" → Did the screen actually go white? Check video.
- "You ignored the dropped weapon" → Was this YOUR weapon or an enemy's weapon? Was player alive?
- "You crouched and sprayed" → Did the viewpoint actually lower? Check video.
- "You wide-swung after the kill" → Did POV player get the kill? Check POV PLAYER ACTIONS.
- "You sprayed through smoke" → Was POV player alive and holding the weapon? Check timeline.
- "You should have traded your teammate" → Was POV player even alive? Or spectating?
- "You missed the flash/smoke" → Check GRENADE USAGE - was a grenade actually thrown by POV?
- "You rotated too late" → Was player alive during this? Check death time.
- Any tip about post-death gameplay → AUTO-REJECT (spectating footage)

### DEMO DATA IS AUTHORITATIVE

The POV PLAYER ACTIONS section lists EXACTLY what the player did according to the demo file.
If a tip claims an action that isn't in this list, it's either:
1. A teammate's action (misattributed)
2. An enemy's action
3. A hallucination (never happened)

In ALL these cases: REJECT THE TIP."""

        return base_prompt

    def _build_verification_prompt(self, analyst_output: AnalystOutput) -> str:
        """Build the verification prompt."""
        # Format tips for verification
        tips_lines = []
        for tip in analyst_output.tips:
            ts_str = tip.timestamp.display if tip.timestamp else "general"
            ts_sec = tip.timestamp.video_seconds if tip.timestamp else 0
            tips_lines.append(f"""
### {tip.id} [{ts_str}] ({tip.category}) - {tip.severity}
- Observation: {tip.observation}
- Why it matters: {tip.why_it_matters}
- Fix: {tip.fix}
- Reasoning: {tip.reasoning or 'Not provided'}
- Timestamp seconds: {ts_sec}
""")

        tips_text = "\n".join(tips_lines) if tips_lines else "No tips to verify."

        # Format rounds timeline if available
        rounds_text = ""
        if analyst_output.rounds_timeline:
            rounds_lines = ["## ROUNDS TIMELINE (use for death verification)"]
            rounds_lines.append("")
            rounds_lines.append(
                "IMPORTANT: Tips occurring AFTER death_seconds are INVALID (player was spectating)"
            )
            rounds_lines.append("")
            for r in analyst_output.rounds_timeline:
                round_num = r.get("round", "?")
                start = r.get("start_seconds", 0)
                end = r.get("end_seconds", 0)
                death = r.get("death_seconds")
                if death is not None:
                    death_str = f"DIED at {death}s"
                    valid_range = f"(tips valid: {start}s-{death}s)"
                else:
                    death_str = "SURVIVED"
                    valid_range = f"(tips valid: {start}s-{end}s)"
                rounds_lines.append(
                    f"  Round {round_num}: {start}s - {end}s | {death_str} {valid_range}"
                )
            rounds_text = "\n".join(rounds_lines)
        else:
            rounds_text = "## ROUNDS TIMELINE\n\nNo rounds data available - verify tips manually against video."

        # Format replay data
        replay_info = self.format_replay_data_for_prompt()

        prompt = f"""
## REPLAY DATA

{replay_info}

{rounds_text}

## TIPS TO VERIFY ({len(analyst_output.tips)} total)

{tips_text}

## TASK

For each tip above:
1. Go to the timestamp in the video
2. Watch 5 seconds before and after
3. Verify what the tip describes actually happened
4. Check if player was alive at that moment (use rounds timeline)
5. Assign a confidence score (1-10)

Keep tips with confidence >= 8.
Remove tips with confidence < 8.

Create a 100-300 character summary for the key improvements.

Return your verification as JSON.
"""
        return prompt

    def _parse_verification_response(self, response_text: str) -> VerifierOutput:
        """Parse the verification response."""
        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[{self.name}] Could not parse verification JSON")
            return VerifierOutput(
                verified_tips=[],
                removed_tips=[],
                summary_text="Verification failed. Please try again.",
            )

        # Parse verified tips
        verified_tips = []
        for tip in data.get("verified_tips", []):
            try:
                ts = tip.get("timestamp")
                timestamp = None
                if ts:
                    timestamp = Timestamp(
                        video_seconds=ts.get("video_seconds", 0),
                        display=ts.get("display", "0:00"),
                    )

                verified_tips.append(
                    VerifiedTip(
                        id=tip.get("id", f"tip_{len(verified_tips)+1:03d}"),
                        timestamp=timestamp,
                        category=tip.get("category", "general"),
                        tip_text=tip.get("tip_text", ""),
                        severity=tip.get("severity", "important"),
                        source=tip.get("source", "analyst"),
                        confidence=tip.get("confidence", 8),
                        verification_notes=tip.get("verification_notes"),
                    )
                )
                logger.info(
                    f"[{self.name}] Verified: {tip.get('id', '?')} "
                    f"(confidence={tip.get('confidence', '?')})"
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Error parsing verified tip: {e}")

        # Parse removed tips
        removed_tips = []
        for tip in data.get("removed_tips", []):
            try:
                removed_tips.append(
                    RemovedTip(
                        id=tip.get("id", "unknown"),
                        reason=tip.get("reason", "Unknown reason"),
                        confidence=tip.get("confidence", 1),
                    )
                )
                logger.info(
                    f"[{self.name}] Removed: {tip.get('id', '?')} - {tip.get('reason', '?')}"
                )
            except Exception as e:
                logger.warning(f"[{self.name}] Error parsing removed tip: {e}")

        # Get summary
        summary_text = data.get("summary_text", "Analysis complete.")

        # Validate summary length
        if len(summary_text) < 50:
            summary_text = "Analysis complete. Check the tips below for improvement areas."
        elif len(summary_text) > 400:
            summary_text = summary_text[:397] + "..."

        return VerifierOutput(
            verified_tips=verified_tips,
            removed_tips=removed_tips,
            summary_text=summary_text,
        )
