"""
Forging API - AI-powered game analysis for esports improvement
"""
import logging
import os
import tempfile

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
    VideoAnalysisResponse,
)
from services.aoe2_parser import parse_aoe2_replay
from services.cs2_parser import parse_cs2_demo
from services.analyzer import analyze_with_gemini, list_available_models
from services import gcs
from services import video_analyzer
from services import cs2_video_analyzer
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
