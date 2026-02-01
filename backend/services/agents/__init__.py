"""
Base Agent Infrastructure

This module provides the base class and utilities for game-specific agents.
Game-specific agents are now in the pipelines module:
- services.pipelines.cs2 (CS2ObserverAgent, CS2ValidatorAgent)
- services.pipelines.aoe2 (AoE2ObserverAgent, AoE2ValidatorAgent)
"""

from .base import BaseAgent, get_gemini_client, upload_video_to_gemini

__all__ = [
    "BaseAgent",
    "get_gemini_client",
    "upload_video_to_gemini",
]
