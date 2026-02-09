"""
Data contracts for the AoE2 pipeline.

Defines the data structures passed between Observer and Validator agents.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class Timestamp(BaseModel):
    """Timestamp with video time and optional display format."""

    video_seconds: int = Field(..., description="Seconds into the video")
    display: str = Field(..., description="Human-readable format like '2:30'")
    game_time: Optional[str] = Field(
        None, description="Game time (may differ from video time due to speed)"
    )


class AoE2ObserverTip(BaseModel):
    """A tip from the AoE2 Observer agent's multi-angle analysis."""

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


class AoE2ObserverOutput(BaseModel):
    """Output from the AoE2 Observer agent."""

    tips: list[AoE2ObserverTip] = Field(
        default_factory=list, description="All tips from multi-angle analysis"
    )


class AoE2VerifiedTip(BaseModel):
    """A verified coaching tip ready for display."""

    id: str = Field(..., description="Unique ID like 'tip_001'")
    timestamp: Optional[Timestamp] = Field(
        None, description="Video timestamp, if applicable"
    )
    category: str = Field(
        ..., description="Category: economy, military, strategy, etc."
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


class AoE2RemovedTip(BaseModel):
    """A tip that was removed during verification."""

    id: str = Field(..., description="ID of the removed tip")
    reason: str = Field(..., description="Why the tip was removed")
    confidence: int = Field(
        ..., ge=1, le=10, description="Confidence score that led to removal"
    )


class AoE2ValidatorOutput(BaseModel):
    """Output from the AoE2 Validator agent."""

    verified_tips: list[AoE2VerifiedTip] = Field(
        default_factory=list, description="Tips that passed verification (confidence >= 8)"
    )
    removed_tips: list[AoE2RemovedTip] = Field(
        default_factory=list, description="Tips that were removed"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")


class AoE2PipelineOutput(BaseModel):
    """Final output from the AoE2 pipeline."""

    tips: list[AoE2VerifiedTip] = Field(
        default_factory=list, description="All verified tips"
    )
    summary_text: str = Field("", description="100-300 char summary for TTS")
    pipeline_metadata: dict = Field(
        default_factory=dict, description="Pipeline execution stats"
    )
    last_interaction_id: Optional[str] = Field(
        None, description="Last Gemini interaction ID for chat chaining"
    )
