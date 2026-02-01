"""
Forging API - AI-powered game analysis for esports improvement
"""
import asyncio
import logging
import os
import tempfile
import uuid

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    AnalysisResponse, GameSummary, Player, PlayerUptime, Analysis,
    VideoUploadRequest, VideoUploadResponse, VideoDownloadResponse,
    VideoAnalysisResponse, ReplayUploadRequest, ReplayUploadResponse,
    SavedAnalysisRequest, SavedAnalysisResponse, AnalysisListItem,
    AnalysisListResponse, AnalysisDetailResponse, TimestampedTip,
    AnalysisStartResponse, AnalysisStatusResponse,
    CS2Content, AoE2Content, AoE2PlayerTimeline, RoundTimeline,
    DemoParseRequest, DemoParseResponse, DemoPlayer,
    ReplayParseRequest, ReplayParseResponse, ReplayPlayer,
    ChatRequest, ChatResponse,
)
from services.parsers import parse_aoe2_replay, parse_cs2_demo
from services.analyzer import analyze_with_gemini, list_available_models
from services import gcs
from services import firestore
from services import thumbnail
from services.llm.gemini import GeminiProvider
from services.agents.base import get_gemini_client, upload_video_to_gemini
from services.pipelines import PipelineFactory

list_available_models()


from typing import Callable, Awaitable, Any


def sanitize_for_firestore(data: Any) -> Any:
    """
    Recursively sanitize data for Firestore storage.

    Firestore doesn't accept:
    - Empty string keys in dicts
    - None keys in dicts

    This function removes or renames such keys.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            # Skip empty or None keys
            if k == "" or k is None:
                continue
            # Ensure key is a string
            key = str(k) if not isinstance(k, str) else k
            sanitized[key] = sanitize_for_firestore(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_firestore(item) for item in data]
    else:
        return data


async def run_analysis_pipeline(
    video_object_name: str,
    replay_data: dict,
    game_type: str = "cs2",
    on_stage_change: Callable[[str], Awaitable[None]] | None = None,
) -> tuple[VideoAnalysisResponse, dict, dict]:
    """
    Run the game-specific analysis pipeline.

    Uses PipelineFactory to create the appropriate pipeline for the game type.

    Args:
        video_object_name: GCS object name for the video
        replay_data: Parsed replay/demo data
        game_type: 'cs2' or 'aoe2'
        on_stage_change: Optional callback to report stage changes

    Returns:
        Tuple of (VideoAnalysisResponse, pipeline_metadata, gemini_file_info)
    """
    # Download video from GCS (async to not block event loop)
    video_tmp_path = await gcs.download_to_temp_async(video_object_name)

    # Stage: Uploading video to Gemini
    if on_stage_change:
        await on_stage_change("uploading_video")

    # Upload video to Gemini
    client = get_gemini_client()
    video_file = await upload_video_to_gemini(client, video_tmp_path)

    try:
        # Stage: Analyzing gameplay
        if on_stage_change:
            await on_stage_change("analyzing")

        # Create and run game-specific pipeline
        pipeline = PipelineFactory.create(game_type, video_file, replay_data)
        output = await pipeline.analyze()

        # Convert pipeline tips to TimestampedTip
        # Get reasoning from observer output (matched by tip ID)
        observer_output = output.metadata.get("observer_output", {})
        observer_tips_by_id = {
            t.get("id"): t for t in observer_output.get("tips", [])
        }

        tips = []
        for tip in output.tips:
            # Get reasoning from observer tip (validator doesn't have it)
            observer_tip = observer_tips_by_id.get(tip.id, {})
            reasoning = observer_tip.get("reasoning")

            tips.append(TimestampedTip(
                timestamp_seconds=tip.timestamp.video_seconds if tip.timestamp else 0,
                timestamp_display=tip.timestamp.display if tip.timestamp else "0:00",
                tip=tip.tip_text,
                category=tip.category,
                reasoning=reasoning,
                confidence=tip.confidence if hasattr(tip, "confidence") else None,
            ))

        # Build game-specific content
        cs2_content = None
        aoe2_content = None

        if game_type == "cs2":
            # Extract rounds_timeline from metadata
            rounds_timeline_raw = output.metadata.get("rounds_timeline", [])
            rounds_timeline = [RoundTimeline(**r) for r in rounds_timeline_raw]
            cs2_content = CS2Content(rounds_timeline=rounds_timeline)
        elif game_type == "aoe2":
            # Build player timeline from replay data (authoritative age-up times)
            players_timeline = []
            pov_player = replay_data.get("pov_player") if replay_data else None
            pov_player_index = None

            if replay_data and "summary" in replay_data:
                for i, player in enumerate(replay_data["summary"].get("players", [])):
                    uptime = player.get("uptime", {})
                    player_name = player.get("name", "Unknown")

                    # Track POV player index
                    if pov_player and player_name.lower() == pov_player.lower():
                        pov_player_index = i

                    players_timeline.append(AoE2PlayerTimeline(
                        name=player_name,
                        civilization=player.get("civilization", "Unknown"),
                        color=player.get("color", "Unknown"),
                        winner=player.get("winner", False),
                        feudal_age_seconds=uptime.get("feudal_age") or uptime.get("feudal_age_age"),
                        castle_age_seconds=uptime.get("castle_age") or uptime.get("castle_age_age"),
                        imperial_age_seconds=uptime.get("imperial_age") or uptime.get("imperial_age_age"),
                    ))
            aoe2_content = AoE2Content(
                players_timeline=players_timeline,
                pov_player_index=pov_player_index,
            )

        response = VideoAnalysisResponse(
            video_object_name=video_object_name,
            duration_seconds=0,
            tips=tips,
            model_used="gemini-3-pro-preview",
            provider="gemini",
            cs2_content=cs2_content,
            aoe2_content=aoe2_content,
        )

        # Include summary_text in metadata for storage
        metadata = {
            **output.metadata,
            "summary_text": output.summary_text,
        }

        # Return video file info for chat use (file expires after 48h)
        gemini_file_info = {
            "uri": video_file.uri,
            "name": video_file.name,
        }

        return response, metadata, gemini_file_info

    finally:
        # Cleanup local temp file only
        # Keep Gemini video file for chat use (expires after 48h anyway)
        if os.path.exists(video_tmp_path):
            os.unlink(video_tmp_path)


app = FastAPI(
    title="Forging API",
    description="AI-powered game analysis for esports improvement",
    version="0.1.0"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return proper JSON response with CORS headers."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


@app.get("/")
async def root():
    return {"message": "Forging API - AI Game Coach", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/analyze/aoe2", response_model=AnalysisResponse)
async def analyze_aoe2(replay: UploadFile = File(...)) -> AnalysisResponse:
    """Analyze an Age of Empires II replay file."""
    if not replay.filename.endswith(".aoe2record"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Expected .aoe2record file"
        )

    content = await replay.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".aoe2record") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        game_data = parse_aoe2_replay(tmp_path)
        analysis_result = await analyze_with_gemini(game_type="aoe2", game_data=game_data)

        # Convert to typed models
        summary = game_data.get("summary", {})
        players = [
            Player(
                name=p.get("name", "Unknown"),
                civilization=p.get("civilization", "Unknown"),
                color=p.get("color", "Unknown"),
                winner=p.get("winner", False),
                rating=p.get("rating", 0),
                eapm=p.get("eapm", 0),
                uptime=PlayerUptime(**p.get("uptime", {})),
            )
            for p in summary.get("players", [])
        ]

        return AnalysisResponse(
            game_type="aoe2",
            game_summary=GameSummary(
                map=summary.get("map", "Unknown"),
                map_size=summary.get("map_size", "Unknown"),
                duration=summary.get("duration", "0:00"),
                game_version=summary.get("game_version", "Unknown"),
                rated=summary.get("rated", False),
                players=players,
            ),
            analysis=Analysis(
                tips=analysis_result.get("tips"),
                raw_analysis=analysis_result.get("raw_analysis"),
                model_used=analysis_result.get("model_used"),
                provider=analysis_result.get("provider"),
                error=analysis_result.get("error"),
            ),
        )
    finally:
        os.unlink(tmp_path)


@app.post("/api/analyze/cs2")
async def analyze_cs2(demo: UploadFile = File(...)):
    """Analyze a Counter-Strike 2 demo file."""
    if not demo.filename.endswith(".dem"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Expected .dem file"
        )

    content = await demo.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dem") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        game_data = parse_cs2_demo(tmp_path)
        analysis = await analyze_with_gemini(game_type="cs2", game_data=game_data)

        return {
            "game_type": "cs2",
            "game_summary": game_data.get("summary", {}),
            "analysis": analysis
        }
    finally:
        os.unlink(tmp_path)


# Video upload endpoints
@app.post("/api/video/upload-url", response_model=VideoUploadResponse)
async def get_video_upload_url(request: VideoUploadRequest) -> VideoUploadResponse:
    """Generate a signed URL for uploading a video to GCS."""
    try:
        result = gcs.generate_upload_url(
            filename=request.filename,
            content_type=request.content_type,
            file_size=request.file_size,
        )
        return VideoUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/video/download-url/{object_name:path}", response_model=VideoDownloadResponse)
async def get_video_download_url(object_name: str) -> VideoDownloadResponse:
    """Generate a signed URL for downloading/playing a video from GCS."""
    try:
        result = gcs.generate_download_url(object_name)
        return VideoDownloadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/video/models")
async def get_video_models():
    """Get list of available video analysis models."""
    return {"models": GeminiProvider.VIDEO_MODELS}


@app.post("/api/analyze/video", response_model=VideoAnalysisResponse)
async def analyze_video_endpoint(
    video_object_name: str = Form(...),
    replay: UploadFile = File(None),
    model: str = Form(None),
    game_type: str = Form("aoe2"),
) -> VideoAnalysisResponse:
    """
    Analyze a gameplay video using Gemini's multimodal capabilities.

    The video should already be uploaded to GCS (via the /api/video/upload-url flow).
    Optionally include a replay/demo file for richer analysis.

    Supported game types:
    - aoe2: Age of Empires II (.aoe2record)
    - cs2: Counter-Strike 2 (.dem)

    This endpoint:
    1. Downloads video from GCS
    2. Uploads it to Gemini File API
    3. Optionally parses the replay/demo for structured game data
    4. Analyzes with Gemini, combining video + replay data
    5. Returns timestamped coaching tips
    """
    replay_data = None
    replay_tmp_path = None

    # Parse replay/demo if provided
    if replay and replay.filename:
        if game_type == "aoe2":
            if not replay.filename.endswith(".aoe2record"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid replay type. Expected .aoe2record file for AoE2"
                )
            suffix = ".aoe2record"
        elif game_type == "cs2":
            if not replay.filename.endswith(".dem"):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid demo type. Expected .dem file for CS2"
                )
            suffix = ".dem"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported game type: {game_type}"
            )

        replay_content = await replay.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(replay_content)
            replay_tmp_path = tmp.name

        try:
            if game_type == "aoe2":
                replay_data = parse_aoe2_replay(replay_tmp_path)
            elif game_type == "cs2":
                replay_data = parse_cs2_demo(replay_tmp_path)
        except Exception as e:
            logger.warning(f"Failed to parse replay/demo: {e}")

    try:
        # Use unified pipeline for all game types
        result, _, _ = await run_analysis_pipeline(
            video_object_name=video_object_name,
            replay_data=replay_data,
            game_type=game_type,
        )

        return result

    finally:
        # Cleanup temp files
        if replay_tmp_path:
            os.unlink(replay_tmp_path)


# Replay upload endpoint
@app.post("/api/replay/upload-url", response_model=ReplayUploadResponse)
async def get_replay_upload_url(request: ReplayUploadRequest) -> ReplayUploadResponse:
    """Generate a signed URL for uploading a replay/demo file to GCS."""
    try:
        result = gcs.generate_replay_upload_url(
            filename=request.filename,
            file_size=request.file_size,
        )
        return ReplayUploadResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Demo parsing endpoint (for POV player selection)
@app.post("/api/demo/parse-players", response_model=DemoParseResponse)
async def parse_demo_players(request: DemoParseRequest) -> DemoParseResponse:
    """Parse a demo file from GCS and return player list."""
    tmp_path = None
    try:
        tmp_path = gcs.download_to_temp(request.demo_object_name)
        demo_data = parse_cs2_demo(tmp_path)
        players = []
        for p in demo_data.get("summary", {}).get("players", []):
            players.append(DemoPlayer(
                name=p.get("name", "Unknown"),
                team=p.get("team") or p.get("starting_side"),
            ))
        return DemoParseResponse(players=players)
    except Exception as e:
        logger.error(f"Failed to parse demo: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse demo: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# Replay parsing endpoint (for AoE2 POV player selection)
@app.post("/api/replay/parse-players", response_model=ReplayParseResponse)
async def parse_replay_players(request: ReplayParseRequest) -> ReplayParseResponse:
    """Parse an AoE2 replay file from GCS and return player list."""
    tmp_path = None
    try:
        tmp_path = gcs.download_to_temp(request.replay_object_name)
        replay_data = parse_aoe2_replay(tmp_path)
        players = []
        for p in replay_data.get("summary", {}).get("players", []):
            players.append(ReplayPlayer(
                name=p.get("name", "Unknown"),
                civilization=p.get("civilization"),
                color=p.get("color"),
            ))
        return ReplayParseResponse(players=players)
    except Exception as e:
        logger.error(f"Failed to parse replay: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse replay: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# Background task to run the actual analysis
async def run_analysis_background(analysis_id: str, request_data: dict):
    """
    Run analysis in the background and update Firestore when complete.

    This runs after the initial response is sent to the client.
    """
    try:
        logger.info(f"Starting background analysis for {analysis_id}")

        # Helper to update stage in Firestore
        async def update_stage(stage: str):
            await firestore.update_analysis(analysis_id, {"stage": stage})

        # Stage 1: Parsing demo/replay
        await update_stage("parsing_demo")

        # Parse replay if provided
        replay_data = None
        replay_tmp_path = None
        game_type = request_data["game_type"]
        video_object_name = request_data["video_object_name"]
        replay_object_name = request_data.get("replay_object_name")
        model = request_data.get("model")

        if replay_object_name:
            try:
                replay_tmp_path = await gcs.download_to_temp_async(replay_object_name)
                if game_type == "aoe2":
                    replay_data = await asyncio.to_thread(parse_aoe2_replay, replay_tmp_path)
                elif game_type == "cs2":
                    replay_data = await asyncio.to_thread(parse_cs2_demo, replay_tmp_path)
            except Exception as e:
                logger.warning(f"Failed to parse replay: {e}")
            finally:
                if replay_tmp_path and os.path.exists(replay_tmp_path):
                    os.unlink(replay_tmp_path)

        # Pass POV player through replay data for CS2
        if replay_data and request_data.get("pov_player"):
            replay_data["pov_player"] = request_data["pov_player"]

        # Run video analysis using unified pipeline (stages 2-5 handled inside)
        result, pipeline_metadata, gemini_file_info = await run_analysis_pipeline(
            video_object_name=video_object_name,
            replay_data=replay_data,
            game_type=game_type,
            on_stage_change=update_stage,
        )

        # Extract player names and game info from replay data
        players = []
        map_name = None
        duration = None
        if replay_data and "summary" in replay_data:
            summary = replay_data["summary"]
            players = [p.get("name", "Unknown") for p in summary.get("players", [])]
            map_name = summary.get("map")
            duration = summary.get("duration")

        # Generate title if not provided
        title = request_data.get("title")
        if not title:
            if players:
                title = f"{game_type.upper()}: {' vs '.join(players[:2])}"
                if map_name:
                    title += f" on {map_name}"
            else:
                title = f"{game_type.upper()} Analysis"

        # Stage: Generating thumbnail
        await update_stage("generating_thumbnail")

        # Generate thumbnail from video at first tip timestamp
        thumbnail_url = None
        video_tmp_path = None
        thumbnail_tmp_path = None
        try:
            if result.tips:
                logger.info("Generating thumbnail from video...")
                video_tmp_path = await gcs.download_to_temp_async(video_object_name)
                tips_for_thumbnail = [{"timestamp": tip.timestamp_display} for tip in result.tips]
                # Run ffmpeg thumbnail extraction in thread pool
                thumbnail_tmp_path = await asyncio.to_thread(
                    thumbnail.extract_thumbnail_from_first_tip,
                    video_tmp_path, tips_for_thumbnail
                )
                if thumbnail_tmp_path:
                    thumbnail_object_name = f"thumbnails/{analysis_id}.jpg"
                    await asyncio.to_thread(
                        gcs.upload_file, thumbnail_tmp_path, thumbnail_object_name, "image/jpeg"
                    )
                    thumbnail_url = thumbnail_object_name
                    logger.info(f"Thumbnail uploaded: {thumbnail_object_name}")
        except Exception as e:
            logger.warning(f"Thumbnail generation failed, using fallback: {e}")
            thumbnail_url = f"fallback/{game_type}.jpg"
        finally:
            if video_tmp_path and os.path.exists(video_tmp_path):
                os.unlink(video_tmp_path)
            if thumbnail_tmp_path and os.path.exists(thumbnail_tmp_path):
                os.unlink(thumbnail_tmp_path)

        # Stage: Generating audio
        audio_object_names = []
        tts_enabled = os.getenv("TTS_ENABLED", "false").lower() == "true"
        if tts_enabled and result.tips:
            await update_stage("generating_audio")
            try:
                from services.tts import generate_tips_audio
                logger.info(f"Generating TTS audio for {len(result.tips)} tips...")
                audio_object_names = generate_tips_audio(
                    [{"tip": tip.tip} for tip in result.tips],
                    analysis_id
                )
                logger.info(f"Generated {len(audio_object_names)} audio files")
            except Exception as e:
                logger.warning(f"TTS generation failed (continuing without audio): {e}")
        else:
            logger.info("TTS generation disabled (set TTS_ENABLED=true to enable)")
                # Continue without audio - not critical

        # Update Firestore with complete analysis
        updates = {
            "status": "complete",
            "stage": None,  # Clear stage on completion
            "title": title,
            "summary_text": pipeline_metadata.get("summary_text", ""),
            "players": players,
            "map": map_name,
            "duration": duration,
            "thumbnail_url": thumbnail_url,
            "tips": [tip.model_dump() for tip in result.tips],
            "tips_count": len(result.tips),
            "game_summary": result.game_summary.model_dump() if result.game_summary else None,
            "model_used": result.model_used,
            "provider": result.provider,
            "audio_object_names": audio_object_names,
            # Store Gemini video file info for chat (expires after 48h)
            "gemini_video_uri": gemini_file_info.get("uri"),
            "gemini_video_name": gemini_file_info.get("name"),
            # Store sanitized replay data for chat context (remove empty keys that break Firestore)
            "parsed_replay_data": sanitize_for_firestore(replay_data) if replay_data else None,
        }

        # Add game-specific content
        if game_type == "cs2" and result.cs2_content:
            updates["cs2_content"] = result.cs2_content.model_dump()
        elif game_type == "aoe2" and result.aoe2_content:
            updates["aoe2_content"] = result.aoe2_content.model_dump()

        await firestore.update_analysis(analysis_id, updates)
        logger.info(f"Background analysis complete for {analysis_id}")

    except Exception as e:
        logger.exception(f"Background analysis failed for {analysis_id}: {e}")
        # Update status to error
        await firestore.update_analysis(analysis_id, {
            "status": "error",
            "error": str(e),
        })


# Saved analysis endpoints
@app.post("/api/analysis", response_model=AnalysisStartResponse)
async def create_analysis(
    request: SavedAnalysisRequest,
) -> AnalysisStartResponse:
    """
    Start a new analysis asynchronously.

    1. Creates a pending analysis record in Firestore
    2. Starts video analysis in background (using asyncio.create_task for true async)
    3. Returns immediately with analysis ID for polling

    The client should redirect to /games/{id} and poll for status.

    Requires both video and replay/demo file for accurate game metadata.
    """
    # Validate that replay file is provided
    if not request.replay_object_name:
        replay_type = ".aoe2record" if request.game_type == "aoe2" else ".dem"
        raise HTTPException(
            status_code=400,
            detail=f"Replay file is required for {request.game_type.upper()} analysis. Please upload a {replay_type} file."
        )

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())[:8]

    # Create initial record with "processing" status
    analysis_record = {
        "id": analysis_id,
        "status": "processing",
        "game_type": request.game_type,
        "title": request.title or f"{request.game_type.upper()} Analysis",
        "creator_name": request.creator_name,
        "video_object_name": request.video_object_name,
        "replay_object_name": request.replay_object_name,
        "is_public": request.is_public,
        # Placeholders for data that will be filled by background task
        "players": [],
        "map": None,
        "duration": None,
        "thumbnail_url": None,
        "tips": [],
        "tips_count": 0,
        "game_summary": None,
        "model_used": None,
        "provider": None,
    }

    await firestore.save_analysis(analysis_record)
    logger.info(f"Created analysis {analysis_id} with status=processing")

    # Start background task using asyncio.create_task for TRUE async execution
    # This returns immediately without waiting for the task to complete
    request_data = {
        "game_type": request.game_type,
        "video_object_name": request.video_object_name,
        "replay_object_name": request.replay_object_name,
        "model": request.model,
        "title": request.title,
        "creator_name": request.creator_name,
        "pov_player": request.pov_player,
    }
    asyncio.create_task(run_analysis_background(analysis_id, request_data))

    # Return immediately
    share_url = f"/games/{analysis_id}"
    return AnalysisStartResponse(
        id=analysis_id,
        status="processing",
        share_url=share_url,
    )


@app.get("/api/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
    """Get the status of an analysis (for polling)."""
    # Use non-blocking status fetch with field masks for fast response
    record = await firestore.get_analysis_status(analysis_id)

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatusResponse(
        id=analysis_id,
        status=record.get("status", "complete"),  # Default to complete for old records
        stage=record.get("stage"),
        error=record.get("error"),
    )


@app.get("/api/analysis/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(analysis_id: str) -> AnalysisDetailResponse:
    """Get a saved analysis by ID."""
    record = await firestore.get_analysis(analysis_id)

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Generate signed URL for video playback
    try:
        video_url_data = gcs.generate_download_url(record["video_object_name"])
        video_signed_url = video_url_data["signed_url"]
    except Exception as e:
        logger.warning(f"Failed to generate video URL: {e}")
        video_signed_url = ""

    # Generate signed URLs for audio files
    audio_urls = []
    for audio_object in record.get("audio_object_names", []):
        try:
            audio_url_data = gcs.generate_download_url(audio_object)
            audio_urls.append(audio_url_data["signed_url"])
        except Exception as e:
            logger.warning(f"Failed to generate audio URL for {audio_object}: {e}")
            audio_urls.append("")  # Keep placeholder for indexing

    # Convert tips back to TimestampedTip objects
    tips = [TimestampedTip(**tip) for tip in record.get("tips", [])]

    # Reconstruct GameSummary if present
    game_summary = None
    if record.get("game_summary"):
        game_summary = GameSummary(**record["game_summary"])

    # Reconstruct game-specific content
    cs2_content = None
    aoe2_content = None
    if record.get("cs2_content"):
        cs2_content = CS2Content(**record["cs2_content"])
    if record.get("aoe2_content"):
        aoe2_content = AoE2Content(**record["aoe2_content"])

    return AnalysisDetailResponse(
        id=record["id"],
        status=record.get("status", "complete"),  # Default to complete for old records
        game_type=record["game_type"],
        title=record["title"],
        summary_text=record.get("summary_text"),
        creator_name=record.get("creator_name"),
        players=record.get("players", []),
        map=record.get("map"),
        duration=record.get("duration"),
        video_signed_url=video_signed_url,
        replay_object_name=record.get("replay_object_name"),
        thumbnail_url=record.get("thumbnail_url"),
        tips=tips,
        tips_count=record.get("tips_count", len(tips)),
        game_summary=game_summary,
        model_used=record.get("model_used"),
        provider=record.get("provider"),
        error=record.get("error"),
        created_at=record["created_at"],
        audio_urls=audio_urls,
        cs2_content=cs2_content,
        aoe2_content=aoe2_content,
    )


@app.get("/api/analyses", response_model=AnalysisListResponse)
async def list_analyses(
    limit: int = 12,
    game_type: str = None,
) -> AnalysisListResponse:
    """List recent public analyses for the community carousel."""
    analyses = await firestore.list_analyses(
        limit=limit,
        game_type=game_type,
        public_only=True,
    )

    # Generate signed URLs for thumbnails
    items = []
    for a in analyses:
        thumbnail_url = a.get("thumbnail_url")
        # If thumbnail is a GCS object (not a fallback), generate signed URL
        if thumbnail_url and thumbnail_url.startswith("thumbnails/"):
            try:
                url_data = gcs.generate_download_url(thumbnail_url)
                a["thumbnail_url"] = url_data["signed_url"]
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail URL for {a.get('id')}: {e}")
                a["thumbnail_url"] = None
        items.append(AnalysisListItem(**a))

    return AnalysisListResponse(
        analyses=items,
        total=len(items),
    )


def build_chat_context(record: dict, replay_data: dict | None) -> str:
    """Build comprehensive context for chat based on analysis data."""
    game_type = record.get("game_type", "game")
    tips = record.get("tips", [])

    # Format all tips with full details
    tips_text = "\n".join([
        f"- {t.get('timestamp_display', '0:00')}: {t.get('tip', '')}\n"
        f"  Category: {t.get('category', 'N/A')}\n"
        f"  Reasoning: {t.get('reasoning', 'N/A')}"
        for t in tips
    ])

    # Format round timeline (CS2)
    rounds_text = ""
    if record.get("cs2_content"):
        rounds = record["cs2_content"].get("rounds_timeline", [])
        rounds_text = "\n".join([
            f"Round {r['round']}: {r.get('start_time', '?')}-{r.get('end_time', '?')} "
            f"({'DIED at ' + r['death_time'] if r.get('death_time') else 'SURVIVED'})"
            for r in rounds
        ])

    # Include key replay data if available
    kills_text = ""
    if replay_data and replay_data.get("kills"):
        pov_player = (replay_data.get("pov_player") or "").lower()
        if pov_player:
            pov_kills = [k for k in replay_data["kills"]
                         if (k.get("attacker") or "").lower() == pov_player]
            pov_deaths = [k for k in replay_data["kills"]
                          if (k.get("victim") or "").lower() == pov_player]
            kills_text = f"POV Player kills: {len(pov_kills)}, Deaths: {len(pov_deaths)}"

    return f"""You are an AI gaming coach analyzing a {game_type.upper()} gameplay video.

## CRITICAL RULES
1. You have access to the FULL VIDEO - you can analyze any moment the user asks about
2. Base answers on what you observe in the video and the data below
3. If asked about a specific timestamp, watch that moment in the video and describe what you see
4. Keep responses concise (2-3 paragraphs max) and actionable

## GAME DATA

Map: {record.get('map', 'Unknown')}
Duration: {record.get('duration', 'Unknown')}
Players: {', '.join(record.get('players', []))}

## ROUND TIMELINE
{rounds_text if rounds_text else 'N/A'}

## ALL COACHING TIPS FROM ANALYSIS
{tips_text if tips_text else 'No tips available'}

## GAMEPLAY STATS
{kills_text if kills_text else 'N/A'}

## YOUR ROLE
- Answer questions about any moment in the video
- Explain why certain plays were good or bad
- Provide specific improvement advice
- Reference exact timestamps when relevant
"""


@app.post("/api/analysis/{analysis_id}/chat", response_model=ChatResponse)
async def chat_with_analysis(analysis_id: str, request: ChatRequest) -> ChatResponse:
    """
    Follow-up chat about an analysis.

    Allows users to ask questions or discuss the analysis with the AI coach.
    Uses Gemini's interaction chaining for context preservation.

    If the Gemini video file is still available (within 48h of analysis),
    the AI can reference specific moments in the video.

    This is session-only (not persisted to Firestore).
    """
    # Get the analysis record for context
    record = await firestore.get_analysis(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get Gemini client
    client = get_gemini_client()

    # Get stored data for rich context
    gemini_video_uri = record.get("gemini_video_uri")
    replay_data = record.get("parsed_replay_data")

    # Build comprehensive system instruction
    system_instruction = build_chat_context(record, replay_data)

    try:
        # Use the same model as the analysis pipeline
        model = os.getenv("TURTLE_MODEL", "gemini-3-pro-preview")

        # Build input - include video if still available
        # Interactions API requires explicit "type" fields
        input_content = []

        # Try to include video reference if URI exists
        video_included = False
        if gemini_video_uri:
            try:
                # Add video as a file reference with explicit type
                input_content.append({
                    "type": "video",
                    "uri": gemini_video_uri,
                    "mime_type": "video/mp4",
                })
                video_included = True
                logger.info(f"Including Gemini video in chat: {gemini_video_uri}")
            except Exception as e:
                logger.warning(f"Failed to include video in chat (may be expired): {e}")

        # Add user message with explicit type
        input_content.append({"type": "text", "text": request.message})

        # Use interaction chaining if we have a previous interaction
        interaction_params = {
            "model": model,
            "input": input_content,
            "system_instruction": system_instruction,
        }

        if request.previous_interaction_id:
            interaction_params["previous_interaction_id"] = request.previous_interaction_id

        # Run synchronous API call in thread pool to avoid blocking event loop
        interaction = await asyncio.to_thread(
            lambda: client.interactions.create(**interaction_params)
        )

        # Extract response text
        response_text = ""
        if hasattr(interaction, "outputs") and interaction.outputs:
            last_output = interaction.outputs[-1]
            if hasattr(last_output, "text"):
                response_text = last_output.text
            elif hasattr(last_output, "parts"):
                for part in last_output.parts:
                    if hasattr(part, "text"):
                        response_text += part.text

        # Add note if video wasn't available
        if not video_included and gemini_video_uri:
            response_text += "\n\n*(Note: Video reference expired. Responses are based on analysis data only.)*"

        return ChatResponse(
            response=response_text,
            interaction_id=interaction.id,
        )

    except Exception as e:
        logger.error(f"Chat failed for {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
