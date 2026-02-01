#!/usr/bin/env python3
"""
CLI tool for video + replay analysis using game-specific pipelines.

Usage:
    python analyze_video.py video.mp4 replay.dem           # CS2
    python analyze_video.py video.mp4 replay.aoe2record    # AoE2
    python analyze_video.py video.mp4 replay.dem --save    # Save to Firestore
    python analyze_video.py video.mp4 replay.dem -v        # Verbose output
    python analyze_video.py video.mp4 replay.dem --log-level INFO  # Debug logging
"""
import argparse
import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from services.parsers import parse_aoe2_replay, parse_cs2_demo
from services.agents.base import get_gemini_client, upload_video_to_gemini
from services.pipelines import PipelineFactory


def detect_game_type(replay_path: Path) -> str:
    """Detect game type from replay file extension."""
    suffix = replay_path.suffix.lower()
    if suffix == ".aoe2record":
        return "aoe2"
    elif suffix == ".dem":
        return "cs2"
    else:
        raise ValueError(f"Unknown replay type: {suffix}. Supported: .aoe2record, .dem")


def parse_replay(file_path: Path, game_type: str) -> dict:
    """Parse replay file based on game type."""
    if game_type == "aoe2":
        return parse_aoe2_replay(str(file_path))
    elif game_type == "cs2":
        return parse_cs2_demo(str(file_path))
    else:
        raise ValueError(f"Unknown game type: {game_type}")


def format_timestamp(seconds: float) -> str:
    """Format seconds as mm:ss."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def print_tips(tips: list, verbose: bool = False):
    """Print timestamped tips to console."""
    if not tips:
        print("\nNo tips generated.")
        return

    print(f"\n{'='*70}")
    print(f"COACHING TIPS ({len(tips)} tips)")
    print(f"{'='*70}\n")

    for i, tip in enumerate(tips, 1):
        # Extract timestamp
        timestamp = tip.timestamp
        if timestamp:
            time_str = timestamp.display if hasattr(timestamp, 'display') else format_timestamp(timestamp.video_seconds)
        else:
            time_str = "0:00"

        # Extract category
        category = getattr(tip, 'category', 'general')

        # Print tip
        print(f"[{time_str}] [{category.upper()}] {tip.tip_text}")
        print()

    if verbose:
        print(f"\n{'='*70}")
        print("RAW TIP DATA:")
        print(f"{'='*70}\n")
        for tip in tips:
            print(tip.model_dump_json(indent=2))
            print()


def print_replay_summary(replay_data: dict, game_type: str):
    """Print replay summary."""
    summary = replay_data.get("summary", {})
    players = summary.get("players", [])

    print(f"\nGame Summary:")
    print(f"  Map: {summary.get('map', 'Unknown')}")

    if game_type == "aoe2":
        print(f"  Duration: {summary.get('duration', 'Unknown')}")
    else:
        print(f"  Rounds: {summary.get('rounds_played', 'Unknown')}")

    print(f"  Players:")
    for p in players:
        if game_type == "aoe2":
            status = "W" if p.get("winner") else "L"
            civ = p.get("civilization", "Unknown")
            print(f"    [{status}] {p.get('name')} ({civ})")
        else:
            k = p.get("total_kills", 0)
            d = p.get("total_deaths", 0)
            print(f"    {p.get('name')}: {k}K/{d}D")


async def save_to_firestore(
    tips: list,
    replay_data: dict,
    game_type: str,
    video_path: str,
    metadata: dict,
) -> str:
    """Save analysis to Firestore and return share URL."""
    from services import firestore

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())[:8]

    # Extract info from replay
    summary = replay_data.get("summary", {})
    players = [p.get("name", "Unknown") for p in summary.get("players", [])]
    map_name = summary.get("map")
    duration = summary.get("duration")

    # Generate title
    if players:
        title = f"{game_type.upper()}: {' vs '.join(players[:2])}"
        if map_name:
            title += f" on {map_name}"
    else:
        title = f"{game_type.upper()} Analysis"

    # Convert tips to dict format
    tips_data = [tip.model_dump() for tip in tips]

    # Build analysis record
    analysis_record = {
        "id": analysis_id,
        "status": "complete",
        "game_type": game_type,
        "title": title,
        "creator_name": "CLI",
        "video_object_name": f"cli/{Path(video_path).name}",  # Placeholder
        "replay_object_name": None,
        "is_public": False,
        "players": players,
        "map": map_name,
        "duration": duration,
        "thumbnail_url": None,
        "tips": tips_data,
        "tips_count": len(tips),
        "game_summary": summary,
        "model_used": metadata.get("model", "gemini-3-pro-preview"),
        "provider": "gemini",
    }

    await firestore.save_analysis(analysis_record)

    return f"/games/{analysis_id}"


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze gameplay video + replay with AI coaching"
    )
    parser.add_argument(
        "video_file",
        type=Path,
        help="Path to video file (.mp4)"
    )
    parser.add_argument(
        "replay_file",
        type=Path,
        help="Path to replay file (.aoe2record or .dem)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save analysis to Firestore and return share URL"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including raw tip data"
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # Validate files exist
    if not args.video_file.exists():
        print(f"Error: Video file not found: {args.video_file}", file=sys.stderr)
        sys.exit(1)

    if not args.replay_file.exists():
        print(f"Error: Replay file not found: {args.replay_file}", file=sys.stderr)
        sys.exit(1)

    # Detect game type from replay extension
    try:
        game_type = detect_game_type(args.replay_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Game type: {game_type.upper()}")
    print(f"Video: {args.video_file}")
    print(f"Replay: {args.replay_file}")

    # Parse replay
    print(f"\nParsing {game_type.upper()} replay...")
    try:
        replay_data = parse_replay(args.replay_file, game_type)
    except Exception as e:
        print(f"Error parsing replay: {e}", file=sys.stderr)
        sys.exit(1)

    print_replay_summary(replay_data, game_type)

    # Upload video to Gemini
    print(f"\nUploading video to Gemini...")
    client = get_gemini_client()
    video_file = await upload_video_to_gemini(client, str(args.video_file))
    print(f"Video uploaded: {video_file.name}")

    try:
        # Create and run pipeline
        print(f"\nRunning {game_type.upper()} analysis pipeline...")
        pipeline = PipelineFactory.create(game_type, video_file, replay_data)
        output = await pipeline.analyze()

        # Print results
        print_tips(output.tips, verbose=args.verbose)

        # Print metadata if verbose
        if args.verbose and output.metadata:
            print(f"\n{'='*70}")
            print("PIPELINE METADATA:")
            print(f"{'='*70}\n")
            for key, value in output.metadata.items():
                if key != "rounds_timeline":  # Skip large nested data
                    print(f"  {key}: {value}")

        # Save to Firestore if requested
        if args.save:
            print(f"\nSaving to Firestore...")
            share_url = await save_to_firestore(
                tips=output.tips,
                replay_data=replay_data,
                game_type=game_type,
                video_path=str(args.video_file),
                metadata=output.metadata,
            )
            print(f"Share URL: {share_url}")

    finally:
        # Cleanup Gemini video file
        try:
            client.files.delete(name=video_file.name)
            logger.info(f"Deleted Gemini video file: {video_file.name}")
        except Exception as e:
            logger.warning(f"Failed to delete Gemini video file: {e}")


if __name__ == "__main__":
    asyncio.run(main())
