"""
Game-specific analysis pipelines.

Each game gets its own pipeline that orchestrates analysis using
game-specific Observer and Validator agents.
"""

from .base import BasePipeline, PipelineOutput
from .factory import PipelineFactory

__all__ = ["BasePipeline", "PipelineOutput", "PipelineFactory"]
