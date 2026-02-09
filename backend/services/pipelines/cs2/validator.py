"""
CS2 Validator Agent - 2-Step Verification with Confidence Scoring.

Verifies tips from the Observer agent:
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
from typing import Any

from services.agents.base import BaseAgent
from services.pipelines.cs2.contracts import (
    CS2ObserverOutput,
    CS2PipelineOutput,
    CS2RemovedTip,
    CS2ValidatorOutput,
    CS2VerifiedTip,
    RoundTimeline,
    Timestamp,
)

logger = logging.getLogger(__name__)


class CS2ValidatorAgent(BaseAgent):
    """
    CS2 Validator: 2-step verification with confidence scoring.

    Uses video: Yes (for verification)
    Thinking level: HIGH (careful verification)
    """

    name = "cs2_validator"
    uses_video = True
    thinking_level = "high"
    include_thoughts = False

    # Structured output schema for native JSON enforcement
    _verification_schema = {
        "type": "object",
        "properties": {
            "verified_tips": {
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
                        "tip_text": {"type": "string"},
                        "source": {"type": "string"},
                        "confidence": {"type": "integer"},
                        "verification_notes": {"type": "string"},
                    },
                    "required": [
                        "id", "timestamp", "category", "severity",
                        "tip_text", "source", "confidence",
                    ],
                },
            },
            "removed_tips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "reason": {"type": "string"},
                        "confidence": {"type": "integer"},
                    },
                    "required": ["id", "reason", "confidence"],
                },
            },
            "summary_text": {"type": "string"},
        },
        "required": ["verified_tips", "removed_tips", "summary_text"],
    }

    def __init__(self, *args, **kwargs):
        """Initialize with CS2 game type."""
        super().__init__(*args, game_type="cs2", **kwargs)

    def get_system_prompt(self) -> str:
        """Not used - Validator uses custom verify method."""
        return ""

    def build_prompt(self, input_data: dict) -> str:
        """Not used - Validator uses custom verify method."""
        return ""

    def parse_response(self, response_text: str, input_data: dict) -> Any:
        """Not used - Validator uses custom verify method."""
        return None

    async def verify(
        self,
        observer_output: CS2ObserverOutput,
        previous_interaction_id: str | None = None,
    ) -> CS2PipelineOutput:
        """
        Verify tips from the Observer and return final output.

        Args:
            observer_output: Output from the CS2 Observer agent
            previous_interaction_id: Observer's interaction ID for context chaining.
                When provided, Gemini has the full Observer context (video, prompts,
                response) server-side, so we don't need to re-send the video.

        Returns:
            CS2PipelineOutput with verified tips and summary
        """
        logger.info(
            f"[GAME-ANALYSIS] [{self.name}] Starting verification of {len(observer_output.tips)} tips"
        )

        # Get demo-built rounds timeline (deterministic, from demo data)
        # This is set by the pipeline after filtering demo data
        demo_rounds_timeline_raw = self.replay_data.get("rounds_timeline_demo", [])
        demo_rounds_timeline = [
            RoundTimeline(**r) if isinstance(r, dict) else r
            for r in demo_rounds_timeline_raw
        ]
        logger.info(
            f"[GAME-ANALYSIS] [{self.name}] Using demo-built timeline with {len(demo_rounds_timeline)} rounds"
        )

        # ======================================================================
        # Pre-filter: Remove tips with timestamps outside alive windows
        # This is deterministic and runs BEFORE sending to LLM
        # ======================================================================
        valid_tips, pre_removed_tips = self._pre_filter_by_alive_time(
            observer_output.tips, demo_rounds_timeline
        )

        logger.info(
            f"[GAME-ANALYSIS] [{self.name}] Pre-filter: {len(observer_output.tips)} -> {len(valid_tips)} tips "
            f"({len(pre_removed_tips)} removed for being outside alive time)"
        )

        # Create a filtered observer output for LLM verification
        from services.pipelines.cs2.contracts import CS2ObserverOutput
        filtered_observer_output = CS2ObserverOutput(
            tips=valid_tips,
            rounds_timeline=observer_output.rounds_timeline,
        )

        # Build verification prompt
        system_prompt = self._get_verification_system_prompt()
        user_prompt = self._build_verification_prompt(filtered_observer_output, demo_rounds_timeline)

        logger.info(f"[GAME-ANALYSIS] [{self.name}] System prompt: {len(system_prompt)} chars")
        logger.info(f"[GAME-ANALYSIS] [{self.name}] User prompt: {len(user_prompt)} chars")

        # Build input content
        # When chaining from Observer, video is already in server context — no need to re-send
        if previous_interaction_id:
            input_content = [{"type": "text", "text": user_prompt}]
            logger.info(
                f"[GAME-ANALYSIS] [{self.name}] Chaining from Observer interaction "
                f"(video already in context, not re-sending)"
            )
        elif self.video_file:
            input_content = [
                {"type": "text", "text": user_prompt},
                {
                    "type": "video",
                    "uri": self.video_file.uri,
                    "mime_type": "video/mp4",
                },
            ]
            logger.info(f"[GAME-ANALYSIS] [{self.name}] Including video: {self.video_file.uri}")
        else:
            input_content = [{"type": "text", "text": user_prompt}]

        # Call the model with structured output
        # Interactions API: response_mime_type and response_format are top-level params,
        # not inside generation_config
        generation_config = {
            "thinking_level": self.thinking_level,
        }
        logger.info(f"[GAME-ANALYSIS] [{self.name}] Using structured output with response_format")

        interaction_params = {
            "model": os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
            "input": input_content,
            "system_instruction": system_prompt,
            "generation_config": generation_config,
            "response_mime_type": "application/json",
            "response_format": self._verification_schema,
        }
        if previous_interaction_id:
            interaction_params["previous_interaction_id"] = previous_interaction_id

        interaction = self.client.interactions.create(**interaction_params)

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

        logger.info(f"[GAME-ANALYSIS] [{self.name}] Verification response: {len(response_text)} chars")

        # Parse the response
        validator_output = self._parse_verification_response(response_text)

        # Build final output
        # Note: rounds_timeline is now set by pipeline from demo data (deterministic),
        # not from LLM output. We pass an empty list here; pipeline will override.
        all_removed_tips = pre_removed_tips + validator_output.removed_tips
        final_output = CS2PipelineOutput(
            tips=validator_output.verified_tips,
            rounds_timeline=demo_rounds_timeline,  # Use demo-built timeline
            summary_text=validator_output.summary_text,
            pipeline_metadata={
                "observer_tips_count": len(observer_output.tips),
                "pre_filtered_count": len(pre_removed_tips),
                "llm_removed_count": len(validator_output.removed_tips),
                "verified_tips_count": len(validator_output.verified_tips),
                "removed_tips_count": len(all_removed_tips),
                "removed_tips": [t.model_dump() for t in all_removed_tips],
            },
            last_interaction_id=interaction.id,
        )

        logger.info(
            f"[GAME-ANALYSIS] [{self.name}] Verification complete: "
            f"{len(validator_output.verified_tips)} verified, "
            f"{len(validator_output.removed_tips)} removed"
        )

        return final_output

    def _get_verification_system_prompt(self) -> str:
        """System prompt for CS2 verification."""
        return """You are a Verifier agent. Your job is to cross-check tips against video evidence.

## VIDEO HUD GUIDE

On the LEFT side of the video, you can see an overlay with:
1. A MINIMAP showing the current map layout
2. Below the minimap: the CURRENT LOCATION of the POV player (e.g., "Long Doors", "A Site", "Mid", "T Spawn")
3. The POV player's NAME is shown in the HUD

Use the location text to verify if the tip's location description is accurate.

## YOUR MISSION

For EACH tip from the Observer:
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

## MINIMUM OUTPUT REQUIREMENT

After verification, ensure at least 1 tip per round remains.
If a round would have zero tips after verification:
- Tips with confidence 7 are borderline - keep them if the observation is basically valid
- Prefer keeping an imperfect tip over having no feedback for a round

## CS2-SPECIFIC RULES

### MANDATORY CROSS-CHECKS (Do ALL of these for EVERY tip)

For EACH tip, you MUST verify against the REPLAY DATA:

**1. DEATH CHECK:**
   - Look up which round this timestamp falls into (use ROUND TIMELINE)
   - If tip_timestamp > death_time for that round -> REJECT (player was spectating)
   - If death_time is null for that round -> player survived, full round is valid

**2. ACTION OWNERSHIP:**
   - Look up in POV PLAYER ACTIONS section
   - If tip says "you threw a flashbang" -> VERIFY the grenade appears in POV's grenades list
   - If tip says "you got a kill" -> VERIFY in POV's kills list
   - If the action is NOT in POV's actions -> REJECT (was teammate/enemy action)

**3. GRENADE TYPE VERIFICATION:**
   - If tip mentions a grenade, cross-check GRENADE USAGE SUMMARY
   - flashbang != smokegrenade != molotov != hegrenade
   - If type mismatch -> REJECT or correct the grenade type

**4. GAME STATE VERIFICATION:**
   - If tip references bomb status (planted/defused):
   - Check ROUND RESULTS for bomb_planted (true/false) and bomb_site
   - If tip says "bomb planted B" but data shows no plant or wrong site -> REJECT

**5. VISUAL VERIFICATION:**
   - If tip says "you were flashed" -> screen MUST go white in video
   - If tip says "you crouched" -> viewpoint MUST lower in video
   - Don't trust assumptions; verify what you actually SEE

### HALLUCINATION RED FLAGS - AUTO-REJECT

These are common fabrications. Be VERY skeptical if you see these:

- "You stood still while flashed" -> Did the screen actually go white? Check video.
- "You ignored the dropped weapon" -> Was this YOUR weapon or an enemy's weapon? Was player alive?
- "You crouched and sprayed" -> Did the viewpoint actually lower? Check video.
- "You wide-swung after the kill" -> Did POV player get the kill? Check POV PLAYER ACTIONS.
- "You sprayed through smoke" -> Was POV player alive and holding the weapon? Check timeline.
- "You should have traded your teammate" -> Was POV player even alive? Or spectating?
- "You missed the flash/smoke" -> Check GRENADE USAGE - was a grenade actually thrown by POV?
- "You rotated too late" -> Was player alive during this? Check death time.
- Any tip about post-death gameplay -> AUTO-REJECT (spectating footage)

### DEMO DATA IS AUTHORITATIVE

The POV PLAYER ACTIONS section lists EXACTLY what the player did according to the demo file.
If a tip claims an action that isn't in this list, it's either:
1. A teammate's action (misattributed)
2. An enemy's action
3. A hallucination (never happened)

In ALL these cases: REJECT THE TIP.

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
      "source": "observer",
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

When creating tip_text from the Observer's observation + fix:
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

Return ONLY valid JSON."""

    def _build_verification_prompt(
        self,
        observer_output: CS2ObserverOutput,
        rounds_timeline: list[RoundTimeline],
    ) -> str:
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

        # Format rounds timeline (from demo data - authoritative)
        rounds_text = ""
        if rounds_timeline:
            rounds_lines = ["## ROUNDS TIMELINE (from demo data - authoritative)"]
            rounds_lines.append("")
            rounds_lines.append(
                "IMPORTANT: Tips occurring AFTER death_seconds are INVALID (player was spectating)"
            )
            rounds_lines.append("")
            for r in rounds_timeline:
                if r.death_seconds is not None:
                    death_str = f"DIED at {r.death_time}"
                    valid_range = f"(tips valid: {r.start_time}-{r.death_time})"
                else:
                    death_str = "SURVIVED"
                    valid_range = f"(tips valid: {r.start_time}-{r.end_time})"
                rounds_lines.append(
                    f"  Round {r.round}: {r.start_time} - {r.end_time} | {death_str} {valid_range}"
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

## TIPS TO VERIFY ({len(observer_output.tips)} total)

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

    def _parse_verification_response(self, response_text: str) -> CS2ValidatorOutput:
        """Parse the verification response."""
        data = self._extract_json(response_text)

        if not data:
            logger.warning(f"[GAME-ANALYSIS] [{self.name}] Could not parse verification JSON")
            return CS2ValidatorOutput(
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
                    CS2VerifiedTip(
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
                    f"[GAME-ANALYSIS] [{self.name}] Verified: {tip.get('id', '?')} "
                    f"(confidence={tip.get('confidence', '?')})"
                )
            except Exception as e:
                logger.warning(f"[GAME-ANALYSIS] [{self.name}] Error parsing verified tip: {e}")

        # Parse removed tips
        removed_tips = []
        for tip in data.get("removed_tips", []):
            try:
                removed_tips.append(
                    CS2RemovedTip(
                        id=tip.get("id", "unknown"),
                        reason=tip.get("reason", "Unknown reason"),
                        confidence=tip.get("confidence", 1),
                    )
                )
                logger.info(
                    f"[GAME-ANALYSIS] [{self.name}] Removed: {tip.get('id', '?')} - {tip.get('reason', '?')}"
                )
            except Exception as e:
                logger.warning(f"[GAME-ANALYSIS] [{self.name}] Error parsing removed tip: {e}")

        # Get summary
        summary_text = data.get("summary_text", "Analysis complete.")

        # Validate summary length
        if len(summary_text) < 50:
            summary_text = "Analysis complete. Check the tips below for improvement areas."
        elif len(summary_text) > 400:
            summary_text = summary_text[:397] + "..."

        return CS2ValidatorOutput(
            verified_tips=verified_tips,
            removed_tips=removed_tips,
            summary_text=summary_text,
        )

    def _pre_filter_by_alive_time(
        self,
        tips: list,
        rounds_timeline: list[RoundTimeline],
    ) -> tuple[list, list[CS2RemovedTip]]:
        """
        Pre-filter tips to remove those outside POV player's alive time.

        This is a deterministic check that runs BEFORE LLM verification.
        Tips with timestamps after the player died are rejected.

        Args:
            tips: List of CS2ObserverTip from observer
            rounds_timeline: Demo-based rounds timeline with death info

        Returns:
            Tuple of (valid_tips, removed_tips)
        """
        if not rounds_timeline:
            # No timeline data - can't filter, pass all through
            return tips, []

        valid_tips = []
        removed_tips = []

        for tip in tips:
            if not tip.timestamp:
                # No timestamp - let LLM decide
                valid_tips.append(tip)
                continue

            timestamp_seconds = tip.timestamp.video_seconds
            is_valid = False

            # Check if timestamp falls within a valid alive window
            for r in rounds_timeline:
                start = r.start_seconds
                # End of valid window is death time (if died) or round end (if survived)
                end = r.death_seconds if r.death_seconds is not None else r.end_seconds

                if start <= timestamp_seconds <= end:
                    is_valid = True
                    break

            if is_valid:
                valid_tips.append(tip)
            else:
                # Find which round this tip was in (if any)
                round_info = ""
                for r in rounds_timeline:
                    if r.start_seconds <= timestamp_seconds <= r.end_seconds:
                        if r.death_seconds is not None:
                            round_info = f" (Round {r.round}: player died at {r.death_time})"
                        break

                removed_tips.append(
                    CS2RemovedTip(
                        id=tip.id,
                        reason=f"Timestamp {tip.timestamp.display} is outside POV player's alive time{round_info}",
                        confidence=0,  # Deterministic rejection
                    )
                )
                logger.info(
                    f"[GAME-ANALYSIS] [{self.name}] Pre-filtered: {tip.id} at {tip.timestamp.display} "
                    f"- outside alive time{round_info}"
                )

        return valid_tips, removed_tips
