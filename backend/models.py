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


# Video upload models
class VideoUploadRequest(BaseModel):
    """Request to generate a signed upload URL."""
    filename: str
    content_type: str  # must be video/mp4
    file_size: int | None = None  # bytes, for validation


class VideoUploadResponse(BaseModel):
    """Response with signed upload URL."""
    signed_url: str
    object_name: str
    expiry_minutes: int
    bucket: str


class VideoDownloadResponse(BaseModel):
    """Response with signed download URL."""
    signed_url: str
    object_name: str
    expiry_minutes: int


# Video analysis models
class TimestampedTip(BaseModel):
    """A coaching tip tied to a specific timestamp in the video."""
    timestamp_seconds: int  # e.g., 125 = 2:05
    timestamp_display: str  # e.g., "2:05"
    tip: str
    category: str  # "economy" | "military" | "strategy"


class VideoAnalysisResponse(BaseModel):
    """Response from video analysis endpoint."""
    model_config = ConfigDict(protected_namespaces=())

    video_object_name: str
    duration_seconds: int
    tips: list[TimestampedTip]
    game_summary: GameSummary | None = None  # From replay parsing if provided
    model_used: str
    provider: str
    error: str | None = None
