"""
Pydantic models for API request/response types.
These models are used to generate OpenAPI schema for TypeScript codegen.
"""
from pydantic import BaseModel, ConfigDict


class PlayerUptime(BaseModel):
    """Age advancement times in seconds."""
    feudal_age: int | None = None
    castle_age: int | None = None
    imperial_age: int | None = None


class Player(BaseModel):
    """Player information from a game."""
    name: str
    civilization: str
    color: str
    winner: bool
    rating: int
    eapm: int
    uptime: PlayerUptime


class GameSummary(BaseModel):
    """High-level game information."""
    map: str
    map_size: str
    duration: str
    game_version: str
    rated: bool
    players: list[Player]


class Analysis(BaseModel):
    """AI analysis results."""
    model_config = ConfigDict(protected_namespaces=())

    tips: list[str] | None = None
    raw_analysis: str | None = None
    model_used: str | None = None
    provider: str | None = None
    error: str | None = None


class AnalysisResponse(BaseModel):
    """Response from the analyze endpoints."""
    game_type: str
    game_summary: GameSummary
    analysis: Analysis
