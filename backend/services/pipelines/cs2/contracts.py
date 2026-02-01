"""
Data contracts for the CS2 pipeline.

Defines the data structures passed between Observer and Validator agents.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Timestamp(BaseModel):
    """Timestamp with video time and optional display format."""

    video_seconds: int = Field(..., description="Seconds into the video")
    display: str = Field(..., description="Human-readable format like '2:30'")
    game_time: Optional[str] = Field(
        None, description="Game-specific time (may differ from video time)"
    )


class RoundTimeline(BaseModel):
    """Timeline entry for a round in CS2."""

    round: int = Field(..., description="Round number")
    start_seconds: float = Field(..., description="Video seconds when round starts")
    start_time: str = Field(..., description="Video timestamp when round starts")
    end_seconds: float = Field(..., description="Video seconds when round ends")
    end_time: str = Field(..., description="Video timestamp when round ends")
    death_seconds: Optional[float] = Field(
        None, description="Video seconds when POV player died"
    )
    death_time: Optional[str] = Field(
        None, description="Video timestamp when POV player died"
    )
    status: str = Field(..., description="SURVIVED or DIED at X:XX")


class CS2ObserverTip(BaseModel):
    """A tip from the CS2 Observer agent's multi-angle analysis."""

    id: str = Field(..., description="Unique ID like 'tip_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="Video timestamp where this was observed"
    )
    category: str = Field(
        ...,
        description="Category: exploitable_pattern, rank_up_habit, missed_adaptation, etc.",
    )
    severity: str = Field("important", description="'critical', 'important', or 'minor'")
    observation: str = Field(..., description="What was observed in the gameplay")
    why_it_matters: str = Field(..., description="Why this is important to fix")
    fix: str = Field(..., description="How to fix or improve")
    reasoning: Optional[str] = Field(
        None, description="Detailed reasoning for why this tip was generated"
    )
    recurring_timestamps: Optional[List[str]] = Field(
        None,
        description="For recurring patterns: list of video timestamps where this was observed",
    )


class CS2ObserverOutput(BaseModel):
    """Output from the CS2 Observer agent."""

    tips: list[CS2ObserverTip] = Field(
        default_factory=list, description="All tips from multi-angle analysis"
    )
    rounds_timeline: list[RoundTimeline] = Field(
        default_factory=list, description="Timeline of rounds with death timestamps"
    )


class CS2VerifiedTip(BaseModel):
    """A verified coaching tip ready for display."""

    id: str = Field(..., description="Unique ID like 'tip_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="Video timestamp, if applicable"
    )
    category: str = Field(
        ..., description="Category: positioning, awareness, economy, etc."
    )
    tip_text: str = Field(..., description="The actual coaching tip text")
    severity: str = Field("important", description="'critical', 'important', or 'minor'")
    source: str = Field(
        ...,
        description="Source of this tip: 'observer' or 'validator'",
    )
    confidence: int = Field(
        ..., ge=1, le=10, description="1-10 confidence score from verification"
    )
    verification_notes: Optional[str] = Field(
        None, description="Notes from verification process"
    )


class CS2RemovedTip(BaseModel):
    """A tip that was removed during verification."""

    id: str = Field(..., description="ID of the removed tip")
    reason: str = Field(..., description="Why the tip was removed")
    confidence: int = Field(
        ..., ge=1, le=10, description="Confidence score that led to removal"
    )


class CS2ValidatorOutput(BaseModel):
    """Output from the CS2 Validator agent."""

    verified_tips: list[CS2VerifiedTip] = Field(
        default_factory=list, description="Tips that passed verification (confidence >= 8)"
    )
    removed_tips: list[CS2RemovedTip] = Field(
        default_factory=list, description="Tips that were removed"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")


class CS2PipelineOutput(BaseModel):
    """Final output from the CS2 pipeline."""

    tips: list[CS2VerifiedTip] = Field(
        default_factory=list, description="All verified tips"
    )
    rounds_timeline: list[RoundTimeline] = Field(
        default_factory=list, description="Round timeline for navigation"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")
    pipeline_metadata: dict = Field(
        default_factory=dict, description="Pipeline execution stats"
    )
