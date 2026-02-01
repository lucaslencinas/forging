"""
AoE2 Validator Agent - 2-Step Verification with Confidence Scoring.

Verifies tips from the Observer agent:
1. Video Cross-Check: Go to timestamp, watch 5s before and after
2. Replay Data Cross-Check: Verify events match replay data

Assigns confidence scores 1-10:
- 9-10: Clearly visible in video AND confirmed in replay data
- 8: Visible in video, replay data supports it
- 5-7: Event happened but timestamp may be off OR description doesn't match
- 1-4: Hallucination - event didn't happen or completely wrong

Only tips with confidence >= 8 are returned.
"""

import logging
import os
from typing import Any

from services.agents.base import BaseAgent
from services.pipelines.aoe2.contracts import (
    AoE2ObserverOutput,
    AoE2PipelineOutput,
    AoE2RemovedTip,
    AoE2ValidatorOutput,
    AoE2VerifiedTip,
    Timestamp,
)

logger = logging.getLogger(__name__)


class AoE2ValidatorAgent(BaseAgent):
    """
    AoE2 Validator: 2-step verification with confidence scoring.

    Uses video: Yes (for verification)
    Thinking level: HIGH (careful verification)
    """

    name = "aoe2_validator"
    uses_video = True
    thinking_level = "high"
    include_thoughts = False

    def __init__(self, *args, **kwargs):
        """Initialize with AoE2 game type."""
        super().__init__(*args, game_type="aoe2", **kwargs)

    def get_system_prompt(self) -> str:
        """Not used - Validator uses custom verify method."""
        return ""

    def build_prompt(self, input_data: dict) -> str:
        """Not used - Validator uses custom verify method."""
        return ""

    def parse_response(self, response_text: str, input_data: dict) -> Any:
        """Not used - Validator uses custom verify method."""
        return None

    async def verify(self, observer_output: AoE2ObserverOutput) -> AoE2PipelineOutput:
        """
        Verify tips from the Observer and return final output.

        Args:
            observer_output: Output from the AoE2 Observer agent

        Returns:
            AoE2PipelineOutput with verified tips and summary
        """
        logger.info(
            f"[{self.name}] Starting verification of {len(observer_output.tips)} tips"
        )

        # Build verification prompt
        system_prompt = self._get_verification_system_prompt()
        user_prompt = self._build_verification_prompt(observer_output)

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
        validator_output = self._parse_verification_response(response_text)

        # Build final output
        final_output = AoE2PipelineOutput(
            tips=validator_output.verified_tips,
            summary_text=validator_output.summary_text,
            pipeline_metadata={
                "observer_tips_count": len(observer_output.tips),
                "verified_tips_count": len(validator_output.verified_tips),
                "removed_tips_count": len(validator_output.removed_tips),
                "removed_tips": [t.model_dump() for t in validator_output.removed_tips],
            },
        )

        logger.info(
            f"[{self.name}] Verification complete: "
            f"{len(validator_output.verified_tips)} verified, "
            f"{len(validator_output.removed_tips)} removed"
        )

        return final_output

    def _get_verification_system_prompt(self) -> str:
        """System prompt for AoE2 verification."""
        return """You are a Verifier agent for Age of Empires II gameplay analysis.
Your job is to cross-check tips against video evidence.

## VIDEO HUD GUIDE

The AoE2 DE interface shows critical information:

**TOP LEFT:**
- Resources in order: Wood, Food, Gold, Stone (with current amounts)
- Population: Current / Maximum (e.g., "15/26")

**TOP CENTER:**
- Current Age text (e.g., "Dark Age", "Feudal Age")

**TOP RIGHT:**
- Idle villager button
- Player scores with names

**BOTTOM LEFT:**
- Selected unit/building info panel with production queue

**BOTTOM RIGHT:**
- Minimap showing terrain, units, buildings

Use these to verify tip claims against what you actually SEE.

## YOUR MISSION

For EACH tip from the Observer:
1. Go to the claimed timestamp in the video
2. Watch 5 seconds BEFORE and 5 seconds AFTER the timestamp
3. Verify the described event actually happened
4. Check against REPLAY DATA if applicable
5. Assign a confidence score (1-10)
6. Keep tips with confidence >= 8, remove the rest

## VERIFICATION PROCESS

### Step 1: Video Cross-Check
For each tip:
- Navigate to the timestamp
- Watch the 10-second window (5s before, 5s after)
- Did the described event happen?
- Is the timestamp accurate?
- Is the description accurate?

### Step 2: Replay Data Cross-Check
- Does the tip match what the REPLAY DATA shows?
- If tip says "built 2 archery ranges" but replay shows 1, the tip is inaccurate
- If tip says "researched Loom at 4:00" but replay shows 3:30, check if video timestamp is right

## MANDATORY CROSS-CHECKS (Do ALL of these for EVERY tip)

For EACH tip, you MUST verify:

**1. BUILDING COUNT CHECK:**
- If tip mentions number of buildings (e.g., "2 archery ranges"), verify in REPLAY DATA
- Buildings list in replay data is authoritative
- If count mismatch -> REJECT or correct the count

**2. RESEARCH TIMING CHECK:**
- If tip mentions research timing (e.g., "late Loom"), check REPLAY DATA
- Compare claimed timing vs actual research time in data
- Account for game time vs video time conversion (÷1.5)

**3. AGE-UP TIMING CHECK:**
- If tip mentions age-up timing (e.g., "Feudal at 11:00"), verify in REPLAY DATA
- Compare to standard benchmarks (e.g., 22 pop = ~10:00 game time)
- If timing claim is wrong -> REJECT or correct

**4. RESOURCE FLOATING CHECK:**
- If tip claims "floating resources", you must SEE high resource counts in HUD
- Look at top-left corner of video at claimed timestamp
- 500+ of a resource while not saving for something = floating
- If you can't see resources in HUD at that moment -> cannot verify

**5. IDLE TC CHECK:**
- If tip claims "idle TC", verify TC is visible and not producing
- Look for villager walking out, production bar, or queued units
- If TC is off-screen at claimed timestamp -> cannot fully verify
- Cross-reference with idle time gaps in REPLAY DATA if available

**6. UNIT COMPOSITION CHECK:**
- If tip claims wrong army composition, verify in REPLAY DATA
- Check what units the POV player actually built
- If player built different units than claimed -> REJECT

## HALLUCINATION RED FLAGS - AUTO-REJECT

These are common fabrications. Be VERY skeptical if you see these:

- "You didn't scout the enemy" -> Did you actually SEE the scout's path? Check replay data for scout movements.
- "You floated 1000 food" -> Can you SEE 1000+ food in the HUD? Check the actual timestamp.
- "Your TC was idle for 2 minutes" -> Did you verify this in video? 2 minutes is very long.
- "You made no military units" -> Check REPLAY DATA for unit production. This is rarely true.
- "You didn't wall" -> Check if walls appear in REPLAY DATA or are visible on minimap.
- "You didn't react to the scout" -> Did the scout actually see something important? Verify.
- "You built wrong counter units" -> What did opponent actually build? What did player build?
- "You never lured boar" -> Check REPLAY DATA - boar lures are usually logged.
- Any very specific number claims (e.g., "12 idle villagers") -> Verify you can actually count this.

### REPLAY DATA IS AUTHORITATIVE

The REPLAY DATA section contains parsed information from the game file.
If a tip claims something that contradicts REPLAY DATA, it's either:
1. Observer made an error
2. Observer misread the video
3. Hallucination

In ALL these cases: REJECT THE TIP or correct it if the core insight is valid.

## TIMESTAMP VERIFICATION

Remember the game time vs video time conversion:
- Game time / 1.5 = Video time
- If a tip references game time incorrectly, the video timestamp may be wrong

## CONFIDENCE SCORING

Assign a score 1-10 for each tip:

**9-10: HIGH CONFIDENCE**
- Clearly visible in video
- Timestamp is accurate (within 10 seconds)
- Event is exactly as described
- Matches replay data

**8: GOOD CONFIDENCE**
- Visible in video
- Timestamp is close (within 15 seconds)
- Event mostly matches description
- Consistent with replay data

**5-7: MEDIUM CONFIDENCE (REMOVE)**
- Event happened but timestamp is off by >20 seconds
- OR description doesn't quite match what you see
- OR contradicts replay data

**1-4: LOW CONFIDENCE (REMOVE - HALLUCINATION)**
- Event didn't happen at all
- Complete mismatch with video
- Contradicts replay data entirely
- Describes something that isn't in the video

## RULES FOR REMOVAL

REMOVE a tip if:
- Confidence < 8
- Event is not visible in the 10-second window
- Description contradicts what you see in video
- Tip contradicts REPLAY DATA (authoritative source)
- Tip is about the opponent, not the POV player

DO NOT add new tips - only verify existing ones.

## MINIMUM OUTPUT REQUIREMENT

After verification, ensure at least 3 tips remain.
If you would remove all tips:
- Tips with confidence 7 are borderline - keep them if the observation is basically valid
- Prefer keeping an imperfect tip over having no feedback at all
- A partially correct tip is still useful coaching

## OUTPUT FORMAT

Return JSON:
{
  "verified_tips": [
    {
      "id": "tip_001",
      "timestamp": {"video_seconds": 180, "display": "3:00"},
      "category": "rank_up_habit",
      "severity": "critical",
      "tip_text": "Your Town Center was idle for 30+ seconds multiple times. Queue 2-3 villagers at a time to prevent idle TC.",
      "source": "observer",
      "confidence": 9,
      "verification_notes": "Confirmed TC idle at 1:32, 3:47, and 5:12 in video"
    }
  ],
  "removed_tips": [
    {
      "id": "tip_005",
      "reason": "Replay data shows 1 archery range, not 2 as stated",
      "confidence": 4
    }
  ],
  "summary_text": "100-300 char TTS summary of key improvements..."
}

## TIP TEXT FORMATTING

When creating tip_text from the Observer's observation + fix:
- Be concise but actionable
- Format: "Issue observed. How to fix."
- Example: "Your TC was idle for 30+ seconds multiple times in Dark Age. Queue 2-3 villagers at a time."

## SUMMARY GUIDELINES

Write a 100-300 character summary that:
- Will be read aloud via TTS
- Summarizes the 2-3 most important improvements
- Is conversational and encouraging but honest
- Focuses on what to practice

Example summaries:
- "Your biggest issue is idle TC time. Keep villagers queued and you'll hit Feudal faster, which fixes most of your problems."
- "Focus on scouting earlier and reacting to what you see. You had the information but didn't adjust your strategy."

Return ONLY valid JSON."""

    def _build_verification_prompt(self, observer_output: AoE2ObserverOutput) -> str:
        """Build the verification prompt."""
        # Format tips for verification
        tips_lines = []
        for tip in observer_output.tips:
            ts_str = tip.timestamp.display if tip.timestamp else "general"
            ts_sec = tip.timestamp.video_seconds if tip.timestamp else 0
            tips_lines.append(
                f"""
### {tip.id} [{ts_str}] ({tip.category}) - {tip.severity}
- Observation: {tip.observation}
- Why it matters: {tip.why_it_matters}
- Fix: {tip.fix}
- Reasoning: {tip.reasoning or 'Not provided'}
- Timestamp seconds: {ts_sec}
"""
            )

        tips_text = "\n".join(tips_lines) if tips_lines else "No tips to verify."

        # Format replay data
        replay_info = self.format_replay_data_for_prompt()

        prompt = f"""
## REPLAY DATA (AUTHORITATIVE - USE TO VERIFY CLAIMS)

{replay_info}

## TIPS TO VERIFY ({len(observer_output.tips)} total)

{tips_text}

## TASK

For each tip above:
1. Go to the timestamp in the video
2. Watch 5 seconds before and after
3. Verify what the tip describes actually happened
4. Cross-check against REPLAY DATA
5. Assign a confidence score (1-10)

Keep tips with confidence >= 8.
Remove tips with confidence < 8.

Create a 100-300 character summary for the key improvements.

Return your verification as JSON.
"""
        return prompt

    def _parse_verification_response(self, response_text: str) -> AoE2ValidatorOutput:
        """Parse the verification response."""
        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[{self.name}] Could not parse verification JSON")
            return AoE2ValidatorOutput(
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
                    AoE2VerifiedTip(
                        id=tip.get("id", f"tip_{len(verified_tips)+1:03d}"),
                        timestamp=timestamp,
                        category=tip.get("category", "general"),
                        tip_text=tip.get("tip_text", ""),
                        severity=tip.get("severity", "important"),
                        source=tip.get("source", "observer"),
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
                    AoE2RemovedTip(
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

        return AoE2ValidatorOutput(
            verified_tips=verified_tips,
            removed_tips=removed_tips,
            summary_text=summary_text,
        )
