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

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import AnalysisResponse, GameSummary, Player, PlayerUptime, Analysis
from services.aoe2_parser import parse_aoe2_replay
from services.cs2_parser import parse_cs2_demo
from services.analyzer import analyze_with_gemini, list_available_models

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
