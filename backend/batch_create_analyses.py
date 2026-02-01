#!/usr/bin/env python3
"""
Batch creation script to create analyses from local video/replay files.

Discovers video/replay pairs in sample-replays/test-games/ and creates
proper analyses in Firestore with videos uploaded to GCS.

Usage:
    python batch_create_analyses.py --dry-run           # List files without processing
    python batch_create_analyses.py                     # Process all
    python batch_create_analyses.py --game-type cs2     # CS2 only
    python batch_create_analyses.py --game-type aoe2    # AoE2 only
    python batch_create_analyses.py --delay 60          # Custom delay between analyses
"""
import argparse
import asyncio
import logging
import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from services import gcs, firestore, thumbnail
from services.parsers import parse_aoe2_replay, parse_cs2_demo
from main import run_analysis_pipeline, sanitize_for_firestore

# Base path for test games
TEST_GAMES_DIR = Path(__file__).parent.parent / "sample-replays" / "test-games"


def discover_game_pairs() -> list[dict]:
    """
    Discover video/replay pairs in the test-games directory.

    Returns list of dicts with:
        - folder_name: Name of the game folder
        - game_type: 'cs2' or 'aoe2'
        - video_path: Path to the video file
        - replay_path: Path to the replay/demo file
    """
    pairs = []

    if not TEST_GAMES_DIR.exists():
        logger.error(f"Test games directory not found: {TEST_GAMES_DIR}")
        return pairs

    for folder in TEST_GAMES_DIR.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # Detect game type by folder name or file extensions
        files = list(folder.iterdir())
        file_extensions = {f.suffix.lower() for f in files if f.is_file()}

        if ".dem" in file_extensions:
            game_type = "cs2"
            replay_ext = ".dem"
        elif ".aoe2record" in file_extensions:
            game_type = "aoe2"
            replay_ext = ".aoe2record"
        else:
            logger.debug(f"Skipping {folder_name}: No replay/demo file found")
            continue

        # Find replay file
        replay_files = [f for f in files if f.suffix.lower() == replay_ext]
        if not replay_files:
            logger.warning(f"Skipping {folder_name}: No {replay_ext} file found")
            continue
        replay_path = replay_files[0]

        # Find video file (prefer _compressed.mp4)
        video_files = [f for f in files if f.suffix.lower() == ".mp4"]
        if not video_files:
            logger.warning(f"Skipping {folder_name}: No .mp4 video found")
            continue

        # Prefer compressed videos
        compressed = [f for f in video_files if "_compressed" in f.name.lower()]
        video_path = compressed[0] if compressed else video_files[0]

        pairs.append({
            "folder_name": folder_name,
            "game_type": game_type,
            "video_path": video_path,
            "replay_path": replay_path,
        })

    return pairs


def upload_file_to_gcs(local_path: Path, object_name: str, content_type: str) -> str:
    """Upload a local file to GCS and return the object name."""
    logger.info(f"Uploading {local_path.name} to GCS...")
    gcs.upload_file(str(local_path), object_name, content_type)
    return object_name


async def create_analysis(pair: dict) -> dict:
    """
    Create a single analysis from a video/replay pair.

    Returns dict with analysis_id and success status.
    """
    folder_name = pair["folder_name"]
    game_type = pair["game_type"]
    video_path = pair["video_path"]
    replay_path = pair["replay_path"]

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())[:8]

    logger.info(f"\n{'='*60}")
    logger.info(f"Creating analysis: {analysis_id}")
    logger.info(f"  Folder: {folder_name}")
    logger.info(f"  Game: {game_type.upper()}")
    logger.info(f"  Video: {video_path.name}")
    logger.info(f"  Replay: {replay_path.name}")

    try:
        # Upload video to GCS
        video_object_name = f"videos/{analysis_id}.mp4"
        await asyncio.to_thread(
            upload_file_to_gcs, video_path, video_object_name, "video/mp4"
        )

        # Upload replay to GCS
        replay_ext = replay_path.suffix
        replay_object_name = f"replays/{analysis_id}{replay_ext}"
        await asyncio.to_thread(
            upload_file_to_gcs, replay_path, replay_object_name, "application/octet-stream"
        )

        # Parse replay
        logger.info("Parsing replay...")
        if game_type == "aoe2":
            replay_data = await asyncio.to_thread(parse_aoe2_replay, str(replay_path))
        else:
            replay_data = await asyncio.to_thread(parse_cs2_demo, str(replay_path))

        # Extract player names and game info
        players = []
        map_name = None
        duration = None
        if replay_data and "summary" in replay_data:
            summary = replay_data["summary"]
            players = [p.get("name", "Unknown") for p in summary.get("players", [])]
            map_name = summary.get("map")
            duration = summary.get("duration")

        # Generate title from folder name or player names
        title = folder_name
        if not title and players:
            title = f"{game_type.upper()}: {' vs '.join(players[:2])}"
            if map_name:
                title += f" on {map_name}"

        # Create initial Firestore record
        analysis_record = {
            "id": analysis_id,
            "status": "processing",
            "game_type": game_type,
            "title": title,
            "creator_name": "Demo",
            "video_object_name": video_object_name,
            "replay_object_name": replay_object_name,
            "is_public": True,
            "players": players,
            "map": map_name,
            "duration": duration,
            "thumbnail_url": None,
            "tips": [],
            "tips_count": 0,
        }

        await firestore.save_analysis(analysis_record)
        logger.info(f"Created Firestore record: {analysis_id}")

        # Run analysis pipeline
        logger.info("Running analysis pipeline...")

        async def update_stage(stage: str):
            await firestore.update_analysis(analysis_id, {"stage": stage})
            logger.info(f"  Stage: {stage}")

        result, pipeline_metadata, gemini_file_info = await run_analysis_pipeline(
            video_object_name=video_object_name,
            replay_data=replay_data,
            game_type=game_type,
            on_stage_change=update_stage,
        )

        # Generate thumbnail
        logger.info("Generating thumbnail...")
        thumbnail_url = None
        video_tmp_path = None
        thumbnail_tmp_path = None

        try:
            if result.tips:
                video_tmp_path = await gcs.download_to_temp_async(video_object_name)
                tips_for_thumbnail = [{"timestamp": tip.timestamp_display} for tip in result.tips]
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
                    logger.info(f"  Thumbnail uploaded: {thumbnail_object_name}")
        except Exception as e:
            logger.warning(f"  Thumbnail generation failed: {e}")
            thumbnail_url = f"fallback/{game_type}.jpg"
        finally:
            if video_tmp_path and os.path.exists(video_tmp_path):
                os.unlink(video_tmp_path)
            if thumbnail_tmp_path and os.path.exists(thumbnail_tmp_path):
                os.unlink(thumbnail_tmp_path)

        # Update Firestore with complete analysis
        updates = {
            "status": "complete",
            "stage": None,
            "title": title,
            "summary_text": pipeline_metadata.get("summary_text", ""),
            "thumbnail_url": thumbnail_url,
            "tips": [tip.model_dump() for tip in result.tips],
            "tips_count": len(result.tips),
            "game_summary": result.game_summary.model_dump() if result.game_summary else None,
            "model_used": result.model_used,
            "provider": result.provider,
            "gemini_video_uri": gemini_file_info.get("uri"),
            "gemini_video_name": gemini_file_info.get("name"),
            "parsed_replay_data": sanitize_for_firestore(replay_data) if replay_data else None,
        }

        # Add game-specific content
        if game_type == "cs2" and result.cs2_content:
            updates["cs2_content"] = result.cs2_content.model_dump()
        elif game_type == "aoe2" and result.aoe2_content:
            updates["aoe2_content"] = result.aoe2_content.model_dump()

        await firestore.update_analysis(analysis_id, updates)

        logger.info(f"Analysis complete: {analysis_id} - {len(result.tips)} tips")

        return {
            "analysis_id": analysis_id,
            "folder_name": folder_name,
            "success": True,
            "tips_count": len(result.tips),
        }

    except Exception as e:
        logger.exception(f"Failed to create analysis for {folder_name}: {e}")

        # Update status to error if we created a Firestore record
        try:
            await firestore.update_analysis(analysis_id, {
                "status": "error",
                "error": str(e),
            })
        except Exception:
            pass

        return {
            "analysis_id": analysis_id,
            "folder_name": folder_name,
            "success": False,
            "error": str(e),
        }


async def batch_create(
    game_type_filter: str | None = None,
    delay_seconds: int = 30,
    dry_run: bool = False,
):
    """Create analyses for all discovered game pairs."""
    pairs = discover_game_pairs()

    if game_type_filter:
        pairs = [p for p in pairs if p["game_type"] == game_type_filter]

    if not pairs:
        logger.info("No video/replay pairs found.")
        return

    logger.info(f"Found {len(pairs)} video/replay pairs:")
    for pair in pairs:
        logger.info(f"  - {pair['folder_name']} ({pair['game_type'].upper()})")
        logger.info(f"      Video: {pair['video_path'].name}")
        logger.info(f"      Replay: {pair['replay_path'].name}")

    if dry_run:
        logger.info("\nDry run complete. Use without --dry-run to process.")
        return

    results = []
    for i, pair in enumerate(pairs):
        result = await create_analysis(pair)
        results.append(result)

        # Rate limit delay between analyses (except for last one)
        if i < len(pairs) - 1 and delay_seconds > 0:
            logger.info(f"\nWaiting {delay_seconds}s before next analysis...")
            await asyncio.sleep(delay_seconds)

    # Print summary
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    logger.info("\n" + "=" * 60)
    logger.info("BATCH CREATION COMPLETE")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed: {fail_count}")

    if success_count > 0:
        logger.info("\nCreated analyses:")
        for r in results:
            if r["success"]:
                logger.info(f"  - {r['analysis_id']}: {r['folder_name']} ({r['tips_count']} tips)")

    if fail_count > 0:
        logger.info("\nFailed analyses:")
        for r in results:
            if not r["success"]:
                logger.info(f"  - {r['folder_name']}: {r.get('error', 'Unknown error')}")


def main():
    parser = argparse.ArgumentParser(
        description="Create analyses from local video/replay files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without processing"
    )
    parser.add_argument(
        "--game-type",
        choices=["cs2", "aoe2"],
        help="Only process specific game type"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=30,
        help="Delay in seconds between analyses (default: 30)"
    )

    args = parser.parse_args()

    asyncio.run(batch_create(
        game_type_filter=args.game_type,
        delay_seconds=args.delay,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
