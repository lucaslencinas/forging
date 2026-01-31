"""
Pipeline (2-Agent Architecture)

Simplified pipeline for video game coaching analysis:
- Observer: Single-pass multi-angle analysis (10-20 tips)
- Validator: 2-step verification with confidence scoring

Architecture:
    Video + Replay Data
            |
            v
       +----------+
       | Observer |  (single pass, multi-angle analysis)
       +----+-----+
            |
            v
       +-----------+
       | Validator |  (verify against video, remove hallucinations)
       +----+------+
            |
            v
       Final Output
"""

from .analyst import ObserverAgent
from .base import BaseAgent, get_gemini_client, upload_video_to_gemini
from .contracts import (
    AnalystOutput,
    AnalystTip,
    ProducerOutput,
    RemovedTip,
    Timestamp,
    VerifiedTip,
    VerifierOutput,
    # Legacy exports for backward compatibility
    AdaptationOutput,
    ExploitablePattern,
    MissedAdaptation,
    NextRankOutput,
    OpponentCoachOutput,
    RankUpTip,
)
from .orchestrator import PipelineOrchestrator, run_pipeline
from .verifier import ValidatorAgent

__all__ = [
    # Orchestrator
    "PipelineOrchestrator",
    "run_pipeline",
    # Base
    "BaseAgent",
    "get_gemini_client",
    "upload_video_to_gemini",
    # Agents
    "ObserverAgent",
    "ValidatorAgent",
    # Contracts
    "Timestamp",
    "AnalystTip",
    "AnalystOutput",
    "VerifiedTip",
    "RemovedTip",
    "VerifierOutput",
    "ProducerOutput",
    # Legacy Contracts (for backward compatibility)
    "ExploitablePattern",
    "OpponentCoachOutput",
    "RankUpTip",
    "NextRankOutput",
    "MissedAdaptation",
    "AdaptationOutput",
]
