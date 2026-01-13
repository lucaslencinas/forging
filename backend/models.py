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


# Replay upload models
class ReplayUploadRequest(BaseModel):
    """Request to generate a signed upload URL for replay/demo files."""
    filename: str  # Must end with .aoe2record or .dem
    file_size: int | None = None  # bytes, for validation


class ReplayUploadResponse(BaseModel):
    """Response with signed upload URL for replay/demo files."""
    signed_url: str
    object_name: str
    expiry_minutes: int
    bucket: str


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


# Saved analysis models (for shareable links)
class SavedAnalysisRequest(BaseModel):
    """Request to create and save an analysis."""
    video_object_name: str
    replay_object_name: str | None = None
    game_type: str  # "aoe2" | "cs2"
    model: str | None = None
    title: str | None = None
    creator_name: str | None = None
    is_public: bool = True


class SavedAnalysisResponse(BaseModel):
    """Response with saved analysis data and share URL."""
    model_config = ConfigDict(protected_namespaces=())

    id: str
    share_url: str
    game_type: str
    title: str
    creator_name: str | None = None
    players: list[str] = []
    map: str | None = None
    duration: str | None = None
    video_object_name: str
    replay_object_name: str | None = None
    thumbnail_url: str | None = None
    tips: list[TimestampedTip]
    tips_count: int
    game_summary: GameSummary | None = None
    model_used: str
    provider: str
    created_at: str


class AnalysisListItem(BaseModel):
    """Lightweight analysis data for carousel display."""
    id: str
    game_type: str
    title: str
    creator_name: str | None = None
    thumbnail_url: str | None = None
    tips_count: int
    created_at: str


class AnalysisListResponse(BaseModel):
    """Response with list of analyses."""
    analyses: list[AnalysisListItem]
    total: int


class AnalysisDetailResponse(BaseModel):
    """Full analysis data for viewing a shared analysis."""
    model_config = ConfigDict(protected_namespaces=())

    id: str
    game_type: str
    title: str
    creator_name: str | None = None
    players: list[str] = []
    map: str | None = None
    duration: str | None = None
    video_signed_url: str
    replay_object_name: str | None = None
    thumbnail_url: str | None = None
    tips: list[TimestampedTip]
    tips_count: int
    game_summary: GameSummary | None = None
    model_used: str
    provider: str
    created_at: str
