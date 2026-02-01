"""
Game replay/demo parsers.
"""

from .aoe2 import parse_aoe2_replay
from .cs2 import parse_cs2_demo

__all__ = ["parse_aoe2_replay", "parse_cs2_demo"]
