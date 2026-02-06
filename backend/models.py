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
    reasoning: str | None = None  # AI's reasoning for generating this tip
    confidence: int | None = None  # 1-10 confidence score from verification


# CS2-specific models
class RoundTimeline(BaseModel):
    """Timeline entry for a round in CS2."""
    round: int
    start_seconds: float
    start_time: str  # "0:15"
    end_seconds: float
    end_time: str  # "1:32"
    death_seconds: float | None = None
    death_time: str | None = None
    status: str  # "win", "loss", or "unknown"


class CS2Content(BaseModel):
    """CS2-specific analysis content."""
    rounds_timeline: list[RoundTimeline] = []  # Round navigation data


class AoE2PlayerTimeline(BaseModel):
    """Age progression timeline for a single AoE2 player."""
    name: str
    civilization: str
    color: str
    winner: bool
    # Age-up times in game seconds (from replay parser - authoritative)
    feudal_age_seconds: int | None = None
    castle_age_seconds: int | None = None
    imperial_age_seconds: int | None = None


class AoE2Content(BaseModel):
    """AoE2-specific analysis content."""
    players_timeline: list[AoE2PlayerTimeline] = []  # Per-player age progression
    pov_player_index: int | None = None  # Index of the POV player (0 or 1)


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
    # Game-specific content (discriminated by game_type)
    cs2_content: CS2Content | None = None
    aoe2_content: AoE2Content | None = None


# Analysis status enum
AnalysisStatus = str  # "pending" | "processing" | "complete" | "error"


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
    pov_player: str | None = None  # Username of the POV player for CS2


class AnalysisStartResponse(BaseModel):
    """Response when starting an async analysis."""
    id: str
    status: str  # "processing"
    share_url: str


class AnalysisStatusResponse(BaseModel):
    """Response for checking analysis status."""
    id: str
    status: str  # "pending" | "processing" | "complete" | "error"
    stage: str | None = None  # Current processing stage
    error: str | None = None


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
    players: list[str] = []
    map: str | None = None
    duration: str | None = None
    thumbnail_url: str | None = None
    tips_count: int
    created_at: str


class AnalysisListResponse(BaseModel):
    """Response with list of analyses."""
    analyses: list[AnalysisListItem]
    total: int


# Demo/Replay parsing models (for POV player selection)
class DemoParseRequest(BaseModel):
    """Request to parse demo file for player list."""
    demo_object_name: str


class DemoPlayer(BaseModel):
    """Player info from demo."""
    name: str
    team: str | None = None


class DemoParseResponse(BaseModel):
    """Response with player list from demo."""
    players: list[DemoPlayer]


class ReplayParseRequest(BaseModel):
    """Request to parse replay file for player list."""
    replay_object_name: str


class ReplayPlayer(BaseModel):
    """Player info from AoE2 replay."""
    name: str
    civilization: str | None = None
    color: str | None = None


class ReplayParseResponse(BaseModel):
    """Response with player list from replay."""
    players: list[ReplayPlayer]


class AnalysisDetailResponse(BaseModel):
    """Full analysis data for viewing a shared analysis."""
    model_config = ConfigDict(protected_namespaces=())

    id: str
    status: str = "complete"  # "pending" | "processing" | "complete" | "error"
    game_type: str
    title: str
    summary_text: str | None = None  # 100-300 char AI-generated summary for TTS
    creator_name: str | None = None
    players: list[str] = []
    pov_player: str | None = None  # Username of the POV player
    map: str | None = None
    duration: str | None = None
    video_signed_url: str
    replay_object_name: str | None = None
    thumbnail_url: str | None = None
    tips: list[TimestampedTip] = []
    tips_count: int = 0
    game_summary: GameSummary | None = None
    model_used: str | None = None
    provider: str | None = None
    error: str | None = None
    created_at: str
    audio_urls: list[str] = []  # Signed URLs for tip audio files (TTS)
    # Game-specific content
    cs2_content: CS2Content | None = None
    aoe2_content: AoE2Content | None = None


# Chat models (session-only, no persistence)
class ChatRequest(BaseModel):
    """Request for follow-up chat about the analysis."""
    message: str
    previous_interaction_id: str | None = None  # For chaining follow-up messages


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    response: str
    interaction_id: str  # Can be used for follow-up messages
    follow_up_questions: list[str] = []  # Suggested follow-up questions
