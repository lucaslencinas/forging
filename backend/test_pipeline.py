#!/usr/bin/env python3
"""
CLI tool for testing the Pipeline locally.

This bypasses the frontend, GCS, and Firestore for fast iteration.

Usage:
    # Full pipeline with video + replay
    python test_pipeline.py video.mp4 replay.aoe2record

    # Test individual agents
    python test_pipeline.py video.mp4 replay.aoe2record --agent observer

    # Output to JSON file
    python test_pipeline.py video.mp4 replay.aoe2record --output results.json

    # Verbose mode (show raw responses)
    python test_pipeline.py video.mp4 replay.aoe2record -v
"""
import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Configure logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def detect_game_type(replay_path: Path) -> str:
    """Detect game type from replay file extension."""
    suffix = replay_path.suffix.lower()
    if suffix == ".aoe2record":
        return "aoe2"
    elif suffix == ".dem":
        return "cs2"
    else:
        raise ValueError(f"Unknown file type: {suffix}. Supported: .aoe2record, .dem")


def parse_replay(file_path: Path, game_type: str) -> dict:
    """Parse replay file based on game type."""
    from services.aoe2_parser import parse_aoe2_replay
    from services.cs2_parser import parse_cs2_demo

    if game_type == "aoe2":
        return parse_aoe2_replay(str(file_path))
    elif game_type == "cs2":
        return parse_cs2_demo(str(file_path))
    else:
        raise ValueError(f"Unknown game type: {game_type}")


async def get_or_upload_video(client, video_arg: str):
    """Get existing Gemini file or upload a new one.

    Args:
        client: Gemini client
        video_arg: Either "files/abc123" (existing) or "/path/to/video.mp4" (upload)

    Returns:
        Tuple of (video_file, should_cleanup)
    """
    from services.agents.base import upload_video_to_gemini

    if video_arg.startswith("files/"):
        # Use existing file
        print(f"Using existing Gemini file: {video_arg}")
        video_file = client.files.get(name=video_arg)
        state = video_file.state.name if hasattr(video_file.state, 'name') else str(video_file.state)
        print(f"   State: {state}")
        if state != "ACTIVE":
            print(f"File is not ACTIVE, cannot use", file=sys.stderr)
            sys.exit(1)
        return video_file, False  # Don't cleanup existing files
    else:
        # Upload new file
        print(f"Uploading video to Gemini: {video_arg}")
        video_file = await upload_video_to_gemini(client, video_arg)
        print(f"Video uploaded: {video_file.name}")
        return video_file, True  # Cleanup after use


def print_replay_summary(game_data: dict, game_type: str):
    """Print a summary of the parsed replay."""
    summary = game_data.get("summary", {})
    players = summary.get("players", [])

    print(f"\n{'='*60}")
    print("REPLAY SUMMARY")
    print(f"{'='*60}")
    print(f"  Game: {game_type.upper()}")
    print(f"  Map: {summary.get('map', 'Unknown')}")
    print(f"  Duration: {summary.get('duration', 'Unknown')}")

    # Show score for CS2
    if game_type == "cs2":
        score = summary.get("score", {})
        winning_side = summary.get("winning_side", "Unknown")
        ct_wins = score.get("CT", 0)
        t_wins = score.get("T", 0)
        print(f"  Score: CT {ct_wins} - {t_wins} T")
        if winning_side:
            print(f"  Winner: {winning_side}")

    print(f"  Players:")
    for p in players:
        status = "W" if p.get("winner") else "L"

        # For CS2, show team/side info
        if game_type == "cs2":
            team = p.get("team_name") or p.get("starting_side") or "Unknown"
            starting_side = p.get("starting_side", "")
            side_info = f", started {starting_side}" if starting_side else ""
            stats = ""
            if p.get("total_kills") is not None:
                stats = f" - {p.get('total_kills', 0)}/{p.get('total_deaths', 0)}/{p.get('total_assists', 0)}"
            print(f"    [{status}] {p.get('name')} ({team}{side_info}){stats}")
        else:
            # For AoE2
            civ = p.get("civilization", p.get("team", "Unknown"))
            print(f"    [{status}] {p.get('name')} ({civ})")
    print()


async def test_full_pipeline(
    video_arg: str,
    replay_path: Path,
    game_type: str,
    game_data: dict,
    verbose: bool = False
) -> dict:
    """Run the full pipeline (2-agent architecture)."""
    from services.agents.base import get_gemini_client
    from services.agents.orchestrator import PipelineOrchestrator

    print(f"\n{'='*60}")
    print("PIPELINE - 2-AGENT ARCHITECTURE")
    print(f"{'='*60}")
    print("\nPipeline flow:")
    print("  1. Observer: Multi-angle analysis (10-20 tips)")
    print("     - Exploitable Patterns (from opponent's POV)")
    print("     - Rank-Up Habits (what's holding you back)")
    print("     - Missed Adaptations (information -> reaction)")
    print("  2. Validator: Cross-check with confidence scoring")
    print("     - Video cross-check (5s before/after each timestamp)")
    print("     - POV player verification")
    print("     - Only tips with confidence >= 8 are kept")
    print()

    print("Initializing Gemini client...")
    client = get_gemini_client()

    video_file, should_cleanup = await get_or_upload_video(client, video_arg)

    print("\nRunning full pipeline...")

    orchestrator = PipelineOrchestrator(
        video_file=video_file,
        replay_data=game_data,
        game_type=game_type,
        knowledge_base="",
    )

    try:
        output = await orchestrator.analyze()

        print(f"\nPipeline complete!")
        print(f"   Final tips: {len(output.tips)}")

        # Print summary
        if output.summary_text:
            print(f"\nSUMMARY:")
            print(f"   {output.summary_text}")

        # Print pipeline metadata
        metadata = output.pipeline_metadata
        if metadata:
            print(f"\nPIPELINE STATS:")
            print(f"   Total time: {metadata.get('total_time_seconds', 0):.1f}s")
            print(f"   Observer time: {metadata.get('observer_time_seconds', 0):.1f}s")
            print(f"   Validator time: {metadata.get('validator_time_seconds', 0):.1f}s")
            print(f"   Observer tips: {metadata.get('observer_tips_count', 0)}")
            print(f"   Verified tips: {metadata.get('verified_tips_count', 0)}")
            print(f"   Removed tips: {metadata.get('removed_tips_count', 0)}")

        # Print Observer's raw output
        if metadata and metadata.get("observer_output"):
            observer_out = metadata["observer_output"]
            tips = observer_out.get("tips", [])
            if tips:
                print(f"\n{'='*60}")
                print("OBSERVER OUTPUT (raw, before verification)")
                print(f"{'='*60}")
                for tip in tips:
                    ts = tip.get("timestamp", {})
                    ts_str = ts.get("display", "?") if ts else "general"
                    severity_icon = {"critical": "!!", "important": "!", "minor": "."}.get(tip.get("severity", ""), "*")
                    print(f"\n  [{ts_str}] [{tip.get('category', '?')}] {severity_icon}")
                    print(f"     Observation: {tip.get('observation', '')}")
                    print(f"     Why: {tip.get('why_it_matters', '')}")
                    print(f"     Fix: {tip.get('fix', '')}")
                    if tip.get("reasoning"):
                        print(f"     Reasoning: {tip.get('reasoning', '')}")

        # Print removed tips
        if metadata and metadata.get("removed_tips"):
            removed = metadata["removed_tips"]
            if removed:
                print(f"\n{'='*60}")
                print("REMOVED TIPS (confidence < 8)")
                print(f"{'='*60}")
                for tip in removed:
                    print(f"  - {tip.get('id', '?')}: {tip.get('reason', '?')} (confidence={tip.get('confidence', '?')})")

        # Print final verified tips
        if output.tips:
            print(f"\n{'='*60}")
            print("FINAL VERIFIED TIPS (confidence >= 8)")
            print(f"{'='*60}")
            for tip in output.tips:
                ts_str = tip.timestamp.display if tip.timestamp else "general"
                severity_icon = {"critical": "!!", "important": "!", "minor": "."}.get(tip.severity, "*")
                confidence = tip.confidence
                print(f"\n  [{ts_str}] [{tip.category}] {severity_icon} (confidence={confidence})")
                print(f"     {tip.tip_text}")
                if tip.verification_notes:
                    print(f"     Notes: {tip.verification_notes}")

        # Cleanup (only if we uploaded)
        if should_cleanup:
            print("\nCleaning up video file...")
            try:
                client.files.delete(name=video_file.name)
                print("Video file deleted")
            except Exception as e:
                print(f"Failed to delete video: {e}")
        else:
            print(f"\nKeeping existing file: {video_file.name}")

        return output.model_dump()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error (only if we uploaded)
        if should_cleanup:
            try:
                client.files.delete(name=video_file.name)
            except:
                pass
        raise


async def test_single_agent(
    agent_name: str,
    video_arg: str,
    replay_path: Path,
    game_type: str,
    game_data: dict,
    verbose: bool = False
) -> dict:
    """Test a single agent."""
    print(f"\n{'='*60}")
    print(f"TESTING AGENT: {agent_name.upper()}")
    print(f"{'='*60}")

    # Agent descriptions for 2-agent architecture
    agent_info = {
        "observer": {
            "role": "Multi-Angle Observer",
            "description": "Combines exploitable patterns, rank-up habits, and missed adaptations",
            "question": "What are all the issues with this gameplay?",
            "uses_video": True,
            "thinking_level": "high",
        },
    }

    if agent_name not in agent_info:
        print(f"Unknown agent: {agent_name}")
        print(f"   Available: {', '.join(agent_info.keys())}")
        return {"error": f"Unknown agent: {agent_name}"}

    info = agent_info[agent_name]
    print(f"\n  Role: {info['role']}")
    print(f"  Description: {info['description']}")
    print(f"  Question: \"{info['question']}\"")
    print(f"  Uses Video: {info['uses_video']}")
    print(f"  Thinking Level: {info['thinking_level']}")
    print()

    # Run the agent
    if agent_name == "observer":
        return await _run_observer(video_arg, game_type, game_data, verbose)

    return {"status": "not_implemented", "agent": agent_name}


async def _run_observer(
    video_arg: str,
    game_type: str,
    game_data: dict,
    verbose: bool
) -> dict:
    """Run the Observer agent."""
    from services.agents.base import get_gemini_client
    from services.agents.orchestrator import PipelineOrchestrator

    print("Initializing Gemini client...")
    client = get_gemini_client()

    video_file, should_cleanup = await get_or_upload_video(client, video_arg)

    print("\nRunning Observer (Multi-Angle Analysis)...")
    print("   This may take 30-60 seconds for video analysis...")

    orchestrator = PipelineOrchestrator(
        video_file=video_file,
        replay_data=game_data,
        game_type=game_type,
    )

    try:
        output = await orchestrator.run_observer_only()

        print(f"\nObserver complete!")
        print(f"   Tips found: {len(output.tips)}")

        # Print tips by category
        print(f"\nOBSERVER TIPS (ordered by timestamp):")
        for tip in output.tips:
            ts = tip.timestamp
            ts_str = ts.display if ts else "general"
            severity_icon = {"critical": "!!", "important": "!", "minor": "."}.get(tip.severity, "*")
            print(f"\n  [{ts_str}] [{tip.category}] {severity_icon}")
            print(f"     Observation: {tip.observation}")
            print(f"     Why: {tip.why_it_matters}")
            print(f"     Fix: {tip.fix}")
            if tip.reasoning:
                print(f"     Reasoning: {tip.reasoning}")

        # Print rounds timeline if available (CS2)
        if output.rounds_timeline:
            print(f"\nROUNDS TIMELINE:")
            for r in output.rounds_timeline:
                round_num = r.get("round", "?")
                start = r.get("start_seconds", 0)
                end = r.get("end_seconds", 0)
                death = r.get("death_seconds")
                if death is not None:
                    death_str = f"DIED at {death}s"
                else:
                    death_str = "SURVIVED"
                print(f"  Round {round_num}: {start}s - {end}s | {death_str}")

        # Cleanup (only if we uploaded)
        if should_cleanup:
            print("\nCleaning up video file...")
            try:
                client.files.delete(name=video_file.name)
                print("Video file deleted")
            except Exception as e:
                print(f"Failed to delete video: {e}")

        return output.model_dump()

    except Exception as e:
        print(f"\nError: {e}")
        if should_cleanup:
            try:
                client.files.delete(name=video_file.name)
            except:
                pass
        raise


async def main():
    parser = argparse.ArgumentParser(
        description="Test the Pipeline locally (bypasses frontend/GCS)"
    )
    parser.add_argument(
        "video_file",
        type=str,
        help="Path to video file (.mp4) OR Gemini file name (e.g., files/abc123)"
    )
    parser.add_argument(
        "replay_file",
        type=Path,
        help="Path to replay file (.aoe2record or .dem)"
    )
    parser.add_argument(
        "--agent", "-a",
        choices=["observer"],
        help="Test a single agent instead of full pipeline"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output results to JSON file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including raw responses"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Update log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Check if video_file is a Gemini file reference or local path
    is_gemini_file = args.video_file.startswith("files/")

    # Validate files exist (only for local files)
    if not is_gemini_file and not Path(args.video_file).exists():
        print(f"Video file not found: {args.video_file}", file=sys.stderr)
        sys.exit(1)

    if not args.replay_file.exists():
        print(f"Replay file not found: {args.replay_file}", file=sys.stderr)
        sys.exit(1)

    # Detect game type
    try:
        game_type = detect_game_type(args.replay_file)
    except ValueError as e:
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nGame Type: {game_type.upper()}")
    print(f"Video: {args.video_file}")
    print(f"Replay: {args.replay_file}")

    # Parse replay
    print(f"\nParsing replay file...")
    start_time = time.time()
    try:
        game_data = parse_replay(args.replay_file, game_type)
        parse_time = time.time() - start_time
        print(f"Replay parsed in {parse_time:.2f}s")
    except Exception as e:
        print(f"Failed to parse replay: {e}", file=sys.stderr)
        sys.exit(1)

    # Print replay summary
    print_replay_summary(game_data, game_type)

    # Run pipeline or single agent
    start_time = time.time()

    if args.agent:
        result = await test_single_agent(
            agent_name=args.agent,
            video_arg=args.video_file,
            replay_path=args.replay_file,
            game_type=game_type,
            game_data=game_data,
            verbose=args.verbose
        )
    else:
        result = await test_full_pipeline(
            video_arg=args.video_file,
            replay_path=args.replay_file,
            game_type=game_type,
            game_data=game_data,
            verbose=args.verbose
        )

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.2f}s")

    # Output to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
