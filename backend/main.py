"""
Forging API - AI-powered game analysis for esports improvement
"""
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


# Saved analysis endpoints
@app.post("/api/analysis", response_model=SavedAnalysisResponse)
async def create_analysis(request: SavedAnalysisRequest) -> SavedAnalysisResponse:
    """
    Create and save a new analysis.

    1. Runs video analysis (downloads from GCS, analyzes with Gemini)
    2. Optionally parses replay if provided
    3. Saves results to Firestore
    4. Returns shareable URL
    """
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())[:8]

    # Parse replay if provided
    replay_data = None
    replay_tmp_path = None

    if request.replay_object_name:
        try:
            # Download replay from GCS
            replay_tmp_path = gcs.download_to_temp(request.replay_object_name)

            # Parse based on game type
            if request.game_type == "aoe2":
                replay_data = parse_aoe2_replay(replay_tmp_path)
            elif request.game_type == "cs2":
                replay_data = parse_cs2_demo(replay_tmp_path)
        except Exception as e:
            logger.warning(f"Failed to parse replay: {e}")
        finally:
            if replay_tmp_path and os.path.exists(replay_tmp_path):
                os.unlink(replay_tmp_path)

    try:
        # Run video analysis
        if request.game_type == "cs2":
            result = await cs2_video_analyzer.analyze_cs2_video(
                video_object_name=request.video_object_name,
                demo_data=replay_data,
                duration_seconds=0,
                model=request.model,
            )
        else:
            result = await video_analyzer.analyze_video(
                video_object_name=request.video_object_name,
                replay_data=replay_data,
                duration_seconds=0,
                model=request.model,
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
        title = request.title
        if not title:
            if players:
                title = f"{request.game_type.upper()}: {' vs '.join(players[:2])}"
                if map_name:
                    title += f" on {map_name}"
            else:
                title = f"{request.game_type.upper()} Analysis"

        # Generate thumbnail from video at first tip timestamp
        thumbnail_url = None
        video_tmp_path = None
        thumbnail_tmp_path = None
        try:
            if result.tips:
                logger.info("Generating thumbnail from video...")
                video_tmp_path = gcs.download_to_temp(request.video_object_name)

                # Convert tips to dict format for thumbnail extraction
                tips_for_thumbnail = [{"timestamp": tip.timestamp_display} for tip in result.tips]
                thumbnail_tmp_path = thumbnail.extract_thumbnail_from_first_tip(
                    video_tmp_path, tips_for_thumbnail
                )

                if thumbnail_tmp_path:
                    # Upload thumbnail to GCS
                    thumbnail_object_name = f"thumbnails/{analysis_id}.jpg"
                    gcs.upload_file(thumbnail_tmp_path, thumbnail_object_name, "image/jpeg")
                    thumbnail_url = thumbnail_object_name
                    logger.info(f"Thumbnail uploaded: {thumbnail_object_name}")
        except Exception as e:
            logger.warning(f"Thumbnail generation failed, using fallback: {e}")
            # Fallback to game-specific placeholder
            thumbnail_url = f"fallback/{request.game_type}.jpg"
        finally:
            # Cleanup temp files
            if video_tmp_path and os.path.exists(video_tmp_path):
                os.unlink(video_tmp_path)
            if thumbnail_tmp_path and os.path.exists(thumbnail_tmp_path):
                os.unlink(thumbnail_tmp_path)

        # Save to Firestore
        analysis_record = {
            "id": analysis_id,
            "game_type": request.game_type,
            "title": title,
            "creator_name": request.creator_name,
            "players": players,
            "map": map_name,
            "duration": duration,
            "video_object_name": request.video_object_name,
            "replay_object_name": request.replay_object_name,
            "thumbnail_url": thumbnail_url,
            "tips": [tip.model_dump() for tip in result.tips],
            "tips_count": len(result.tips),
            "game_summary": result.game_summary.model_dump() if result.game_summary else None,
            "model_used": result.model_used,
            "provider": result.provider,
            "is_public": request.is_public,
        }

        await firestore.save_analysis(analysis_record)

        # Build share URL (will be frontend URL in production)
        share_url = f"/games/{analysis_id}"

        return SavedAnalysisResponse(
            id=analysis_id,
            share_url=share_url,
            game_type=request.game_type,
            title=title,
            creator_name=request.creator_name,
            players=players,
            map=map_name,
            duration=duration,
            video_object_name=request.video_object_name,
            replay_object_name=request.replay_object_name,
            thumbnail_url=thumbnail_url,
            tips=result.tips,
            tips_count=len(result.tips),
            game_summary=result.game_summary,
            model_used=result.model_used,
            provider=result.provider,
            created_at=analysis_record["created_at"].isoformat(),
        )

    except Exception as e:
        logger.exception(f"Failed to create analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


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

    # Convert tips back to TimestampedTip objects
    tips = [TimestampedTip(**tip) for tip in record.get("tips", [])]

    # Reconstruct GameSummary if present
    game_summary = None
    if record.get("game_summary"):
        game_summary = GameSummary(**record["game_summary"])

    return AnalysisDetailResponse(
        id=record["id"],
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
        model_used=record["model_used"],
        provider=record["provider"],
        created_at=record["created_at"],
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
