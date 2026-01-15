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
)
from services.aoe2_parser import parse_aoe2_replay
from services.cs2_parser import parse_cs2_demo
from services.analyzer import analyze_with_gemini, list_available_models
from services import gcs
from services import video_analyzer
from services import cs2_video_analyzer
from services import firestore
from services import thumbnail
from services.llm.gemini import GeminiProvider

list_available_models()

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
        # Route to appropriate analyzer based on game type
        if game_type == "cs2":
            result = await cs2_video_analyzer.analyze_cs2_video(
                video_object_name=video_object_name,
                demo_data=replay_data,
                duration_seconds=0,
                model=model,
            )
        else:
            # Default to AoE2
            result = await video_analyzer.analyze_video(
                video_object_name=video_object_name,
                replay_data=replay_data,
                duration_seconds=0,
                model=model,
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


# Background task to run the actual analysis
async def run_analysis_background(analysis_id: str, request_data: dict):
    """
    Run analysis in the background and update Firestore when complete.

    This runs after the initial response is sent to the client.
    """
    try:
        logger.info(f"Starting background analysis for {analysis_id}")

        # Parse replay if provided
        replay_data = None
        replay_tmp_path = None
        game_type = request_data["game_type"]
        video_object_name = request_data["video_object_name"]
        replay_object_name = request_data.get("replay_object_name")
        model = request_data.get("model")

        if replay_object_name:
            try:
                replay_tmp_path = gcs.download_to_temp(replay_object_name)
                if game_type == "aoe2":
                    replay_data = parse_aoe2_replay(replay_tmp_path)
                elif game_type == "cs2":
                    replay_data = parse_cs2_demo(replay_tmp_path)
            except Exception as e:
                logger.warning(f"Failed to parse replay: {e}")
            finally:
                if replay_tmp_path and os.path.exists(replay_tmp_path):
                    os.unlink(replay_tmp_path)

        # Run video analysis
        if game_type == "cs2":
            result = await cs2_video_analyzer.analyze_cs2_video(
                video_object_name=video_object_name,
                demo_data=replay_data,
                duration_seconds=0,
                model=model,
            )
        else:
            # Default to AoE2
            result = await video_analyzer.analyze_video(
                video_object_name=video_object_name,
                replay_data=replay_data,
                duration_seconds=0,
                model=model,
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

        # Generate thumbnail from video at first tip timestamp
        thumbnail_url = None
        video_tmp_path = None
        thumbnail_tmp_path = None
        try:
            if result.tips:
                logger.info("Generating thumbnail from video...")
                video_tmp_path = gcs.download_to_temp(video_object_name)
                tips_for_thumbnail = [{"timestamp": tip.timestamp_display} for tip in result.tips]
                thumbnail_tmp_path = thumbnail.extract_thumbnail_from_first_tip(
                    video_tmp_path, tips_for_thumbnail
                )
                if thumbnail_tmp_path:
                    thumbnail_object_name = f"thumbnails/{analysis_id}.jpg"
                    gcs.upload_file(thumbnail_tmp_path, thumbnail_object_name, "image/jpeg")
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

        # Generate TTS audio for tips
        audio_object_names = []
        if result.tips:
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
                # Continue without audio - not critical

        # Update Firestore with complete analysis
        updates = {
            "status": "complete",
            "title": title,
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
        }
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
    record = await firestore.get_analysis(analysis_id)

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatusResponse(
        id=analysis_id,
        status=record.get("status", "complete"),  # Default to complete for old records
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

    return AnalysisDetailResponse(
        id=record["id"],
        status=record.get("status", "complete"),  # Default to complete for old records
        game_type=record["game_type"],
        title=record["title"],
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
