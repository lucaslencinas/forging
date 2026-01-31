"""
Data contracts for the Pipeline (2-Agent Architecture).

New simplified architecture:
- Analyst: Single-pass multi-angle analysis
- Verifier: 2-step verification with confidence scoring
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# SHARED TYPES
# =============================================================================


class Timestamp(BaseModel):
    """Timestamp with video time and optional display format."""

    video_seconds: int = Field(..., description="Seconds into the video")
    display: str = Field(..., description="Human-readable format like '2:30'")
    game_time: Optional[str] = Field(
        None, description="Game-specific time (may differ from video time)"
    )


# =============================================================================
# ANALYST OUTPUT
# =============================================================================


class AnalystTip(BaseModel):
    """A tip from the Analyst agent's multi-angle analysis."""

    id: str = Field(..., description="Unique ID like 'tip_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="Video timestamp where this was observed"
    )
    category: str = Field(
        ...,
        description="Category: exploitable_pattern, rank_up_habit, missed_adaptation, etc.",
    )
    severity: str = Field(
        "important", description="'critical', 'important', or 'minor'"
    )
    observation: str = Field(..., description="What was observed in the gameplay")
    why_it_matters: str = Field(..., description="Why this is important to fix")
    fix: str = Field(..., description="How to fix or improve")
    reasoning: Optional[str] = Field(
        None, description="Detailed reasoning for why this tip was generated"
    )
    recurring_timestamps: Optional[List[str]] = Field(
        None,
        description="For recurring patterns: list of video timestamps where this was observed (e.g., ['1:23', '2:45', '4:12'])",
    )


class AnalystOutput(BaseModel):
    """Output from the Analyst agent."""

    tips: list[AnalystTip] = Field(
        default_factory=list, description="All tips from multi-angle analysis"
    )
    rounds_timeline: Optional[list[dict]] = Field(
        None, description="CS2: Timeline of rounds with death timestamps"
    )


# =============================================================================
# VERIFIER OUTPUT
# =============================================================================


class VerifiedTip(BaseModel):
    """A final, verified coaching tip ready for display."""

    id: str = Field(..., description="Unique ID like 'tip_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="Video timestamp, if applicable"
    )
    category: str = Field(
        ..., description="Category: positioning, awareness, economy, etc."
    )
    tip_text: str = Field(..., description="The actual coaching tip text")
    severity: str = Field(
        "important", description="'critical', 'important', or 'minor'"
    )
    source: str = Field(
        ...,
        description="Source of this tip: 'analyst' or 'verifier'",
    )
    confidence: int = Field(
        ..., ge=1, le=10, description="1-10 confidence score from verification"
    )
    verification_notes: Optional[str] = Field(
        None, description="Notes from verification process"
    )


class RemovedTip(BaseModel):
    """A tip that was removed during verification."""

    id: str = Field(..., description="ID of the removed tip")
    reason: str = Field(..., description="Why the tip was removed")
    confidence: int = Field(
        ..., ge=1, le=10, description="Confidence score that led to removal"
    )


class VerifierOutput(BaseModel):
    """Output from the Verifier agent."""

    verified_tips: list[VerifiedTip] = Field(
        default_factory=list, description="Tips that passed verification (confidence >= 8)"
    )
    removed_tips: list[RemovedTip] = Field(
        default_factory=list, description="Tips that were removed"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")


# =============================================================================
# PIPELINE OUTPUT (Final)
# =============================================================================


class ProducerOutput(BaseModel):
    """Final output from the pipeline."""

    tips: list[VerifiedTip] = Field(
        default_factory=list, description="All verified tips"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")
    pipeline_metadata: dict = Field(
        default_factory=dict, description="Pipeline execution stats"
    )


# =============================================================================
# LEGACY TYPES (kept for backward compatibility during transition)
# =============================================================================


class ExploitablePattern(BaseModel):
    """A pattern the opponent could exploit (legacy)."""

    id: str = Field(..., description="Unique ID like 'exp_001'")
    timestamp: Timestamp
    pattern: str = Field(..., description="The predictable pattern or bad habit")
    how_to_exploit: str = Field(..., description="How an opponent could exploit this")
    fix: str = Field(..., description="How to fix or vary this pattern")
    reasoning: Optional[str] = Field(
        None, description="Why this pattern was identified as exploitable"
    )


class OpponentCoachOutput(BaseModel):
    """Output from Leonardo (Opponent's Coach) - legacy."""

    patterns: list[ExploitablePattern] = Field(
        default_factory=list, description="exploitable patterns"
    )


class RankUpTip(BaseModel):
    """A tip for ranking up (legacy)."""

    id: str = Field(..., description="Unique ID like 'rank_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="May be general, not timestamp-specific"
    )
    habit: str = Field(..., description="The habit holding the player back")
    impact: str = Field(..., description="Why this matters for ranking up")
    fix: str = Field(..., description="How to fix this habit")
    priority: int = Field(..., ge=1, le=10, description="1 = most important to fix")
    reasoning: Optional[str] = Field(
        None, description="Why this habit was identified as important"
    )


class NextRankOutput(BaseModel):
    """Output from Raphael (Next Rank Coach) - legacy."""

    tips: list[RankUpTip] = Field(
        default_factory=list, description="2-3 tips, ranked by priority"
    )


class MissedAdaptation(BaseModel):
    """A moment where player received info but didn't adapt (legacy)."""

    id: str = Field(..., description="Unique ID like 'adapt_001'")
    timestamp: Timestamp
    information_received: str = Field(
        ..., description="What info the player received (sound, sight, scout)"
    )
    what_you_did: str = Field(..., description="What the player actually did")
    what_you_should_have_done: str = Field(
        ..., description="What the player should have done"
    )
    reasoning: Optional[str] = Field(
        None, description="Why this was identified as a missed adaptation"
    )


class AdaptationOutput(BaseModel):
    """Output from Donatello (Adaptation Analyst) - legacy."""

    missed_adaptations: list[MissedAdaptation] = Field(
        default_factory=list, description="moments where information was ignored"
    )
