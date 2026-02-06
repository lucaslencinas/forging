#!/usr/bin/env python3
"""
Batch testing script for CS2 video analysis using the Gemini Agent Pipeline.

Uses the new 2-agent architecture:
- Analyst: Multi-angle analysis (10-20 tips)
- Verifier: Cross-check with confidence scoring

Discovers video/demo pairs in test folders, runs all analyses with rate limiting,
and outputs detailed markdown files with timestamp validation.

Usage:
    # Run all CS2 analyses
    python batch_test.py

    # Dry run (list videos without running)
    python batch_test.py --dry-run

    # Custom delay between calls (default: 75s)
    python batch_test.py --delay 90

    # Run only specific agents
    python batch_test.py --agents analyst full

    # Custom base path
    python batch_test.py --base-path /path/to/test/videos
"""
import argparse
import asyncio
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default path to test videos
DEFAULT_BASE_PATH = Path(__file__).parent.parent / "sample-replays" / "test-games"

# Agents available for testing (new 2-agent architecture)
AGENTS = ["analyst", "full"]


@dataclass
class VideoTestCase:
    """Represents a video file and its associated demo for testing."""
    video_path: Path
    demo_path: Path
    folder_name: str
    video_name: str
    duration_seconds: Optional[float] = None


def get_video_duration(video_path: Path) -> Optional[float]:
    """Extract video duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning(f"Could not get duration for {video_path}: {e}")
    return None


def discover_videos(base_path: Path) -> list[VideoTestCase]:
    """Discover all video/demo pairs in CS2 test folders."""
    test_cases = []

    # Find all Counter-strike folders
    cs2_folders = sorted(base_path.glob("Counter-strike 2 *"))

    for folder in cs2_folders:
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # Find the demo file in this folder
        demo_files = list(folder.glob("*.dem"))
        if not demo_files:
            logger.warning(f"No .dem file found in {folder_name}, skipping")
            continue

        demo_path = demo_files[0]  # Use first demo file

        # Find all video files in this folder
        video_files = sorted(folder.glob("*_compressed.mp4"))
        if not video_files:
            logger.warning(f"No compressed video files found in {folder_name}, skipping")
            continue

        # Create a test case for each video
        for video_path in video_files:
            video_name = video_path.stem.replace("_compressed", "")
            duration = get_video_duration(video_path)

            test_case = VideoTestCase(
                video_path=video_path,
                demo_path=demo_path,
                folder_name=folder_name,
                video_name=video_name,
                duration_seconds=duration
            )
            test_cases.append(test_case)
            logger.info(f"Found: {video_name} (duration: {duration:.1f}s)" if duration else f"Found: {video_name}")

    return test_cases


def validate_timestamps(result: dict, video_duration: float, agent: Optional[str]) -> list[str]:
    """
    Validate that all timestamps in the result are within video duration.

    Returns list of warning messages for any timestamps that exceed duration.
    """
    warnings = []

    if video_duration is None or video_duration <= 0:
        return warnings

    # Collect all items with timestamps based on agent type
    items_to_check = []

    if agent == "analyst":
        # Analyst returns tips with observation field
        tips = result.get("tips", [])
        for t in tips:
            ts = t.get("timestamp")
            if ts:
                items_to_check.append((ts, t.get("observation", "tip")[:50]))
    else:
        # Full pipeline - check verified tips
        tips = result.get("tips", [])
        for tip in tips:
            ts = tip.get("timestamp")
            if ts:
                items_to_check.append((ts, tip.get("tip_text", "tip")[:50]))

    # Check each timestamp
    for ts, context in items_to_check:
        video_seconds = ts.get("video_seconds", 0)
        if video_seconds > video_duration:
            display = ts.get("display", f"{video_seconds}s")
            warnings.append(
                f"Timestamp {display} ({video_seconds}s) exceeds video duration "
                f"({video_duration:.0f}s) - possible hallucination: '{context[:40]}...'"
            )

    return warnings


def format_as_markdown(
    result: dict,
    agent: Optional[str],
    video_name: str,
    video_duration: Optional[float],
    elapsed_seconds: float,
    timestamp_warnings: list[str]
) -> str:
    """Format analysis result as detailed markdown."""
    lines = []

    # Header
    agent_display = agent.capitalize() if agent else "Full Pipeline"
    lines.append(f"# Analysis: {video_name}")
    lines.append(f"**Agent:** {agent_display}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if video_duration:
        mins = int(video_duration // 60)
        secs = int(video_duration % 60)
        lines.append(f"**Video Duration:** {mins}:{secs:02d} ({video_duration:.1f}s)")
    lines.append(f"**Analysis Time:** {elapsed_seconds:.1f}s")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Global timestamp warnings
    if timestamp_warnings:
        lines.append("## Timestamp Warnings")
        lines.append("")
        for warning in timestamp_warnings:
            lines.append(f"> WARNING: {warning}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Format based on agent type
    if agent == "analyst":
        lines.extend(_format_analyst_output(result, video_duration))
    else:
        lines.extend(_format_full_pipeline_output(result, video_duration))

    return "\n".join(lines)


def _format_timestamp_warning(video_seconds: int, video_duration: Optional[float]) -> str:
    """Return warning string if timestamp exceeds duration."""
    if video_duration and video_seconds > video_duration:
        return f"\n> WARNING: Timestamp {video_seconds}s exceeds video duration ({video_duration:.0f}s) - possible hallucination"
    return ""


def _format_analyst_output(result: dict, video_duration: Optional[float]) -> list[str]:
    """Format Analyst's multi-angle analysis output."""
    lines = ["## Analyst Tips (Before Verification)", ""]

    tips = result.get("tips", [])
    if not tips:
        lines.append("*No tips found*")
        return lines

    # Group by category
    by_category = {}
    for tip in tips:
        cat = tip.get("category", "general")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tip)

    for category, category_tips in sorted(by_category.items()):
        lines.append(f"### {category.replace('_', ' ').title()} ({len(category_tips)} tips)")
        lines.append("")

        for tip in category_tips:
            ts = tip.get("timestamp", {})
            ts_display = ts.get("display", "general") if ts else "general"
            video_seconds = ts.get("video_seconds", 0) if ts else 0
            severity = tip.get("severity", "important")
            severity_icon = {"critical": "CRITICAL", "important": "IMPORTANT", "minor": "MINOR"}.get(severity, "")

            lines.append(f"#### [{severity_icon}] @ {ts_display}")
            lines.append(f"**Observation:** {tip.get('observation', 'N/A')}")
            lines.append("")
            lines.append(f"**Why it matters:** {tip.get('why_it_matters', 'N/A')}")
            lines.append("")
            lines.append(f"**Fix:** {tip.get('fix', 'N/A')}")
            lines.append("")

            if tip.get("reasoning"):
                lines.append("<details>")
                lines.append("<summary>Reasoning</summary>")
                lines.append("")
                lines.append(tip.get("reasoning", ""))
                lines.append("")
                lines.append("</details>")
                lines.append("")

            if ts:
                warning = _format_timestamp_warning(video_seconds, video_duration)
                if warning:
                    lines.append(warning)
                    lines.append("")

            lines.append("---")
            lines.append("")

    # Rounds timeline if available
    rounds = result.get("rounds_timeline", [])
    if rounds:
        lines.append("## Rounds Timeline")
        lines.append("")
        lines.append("| Round | Start | Death | End | Status |")
        lines.append("|-------|-------|-------|-----|--------|")
        for r in rounds:
            round_num = r.get("round", "?")
            start = r.get("start_seconds", 0)
            end = r.get("end_seconds", 0)
            death = r.get("death_seconds")
            status = f"DIED @ {death}s" if death else "SURVIVED"
            lines.append(f"| {round_num} | {start}s | {death or '-'} | {end}s | {status} |")
        lines.append("")

    return lines


def _format_full_pipeline_output(result: dict, video_duration: Optional[float]) -> list[str]:
    """Format full pipeline output with verified tips and metadata."""
    lines = []

    # Summary
    summary = result.get("summary_text", "")
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("---")
        lines.append("")

    # Pipeline metadata
    metadata = result.get("pipeline_metadata", {})
    if metadata:
        lines.append("## Pipeline Stats")
        lines.append("")
        lines.append(f"- **Total time:** {metadata.get('total_time_seconds', 0):.1f}s")
        lines.append(f"- **Analyst time:** {metadata.get('analyst_time_seconds', 0):.1f}s")
        lines.append(f"- **Verifier time:** {metadata.get('verifier_time_seconds', 0):.1f}s")
        lines.append(f"- **Analyst tips:** {metadata.get('analyst_tips_count', 0)}")
        lines.append(f"- **Verified tips:** {metadata.get('verified_tips_count', 0)}")
        lines.append(f"- **Removed tips:** {metadata.get('removed_tips_count', 0)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Final verified tips
    tips = result.get("tips", [])
    if tips:
        lines.append("## Final Verified Tips")
        lines.append("")

        for tip in tips:
            ts = tip.get("timestamp", {})
            ts_display = ts.get("display", "general") if ts else "general"
            video_seconds = ts.get("video_seconds", 0) if ts else 0

            severity = tip.get("severity", "important")
            severity_icon = {"critical": "CRITICAL", "important": "IMPORTANT", "minor": "MINOR"}.get(severity, "")
            category = tip.get("category", "general")
            confidence = tip.get("confidence", "?")

            lines.append(f"### [{severity_icon}] {category} @ {ts_display}")
            lines.append(f"**Confidence:** {confidence}/10")
            lines.append("")
            lines.append(f"**Tip:** {tip.get('tip_text', 'N/A')}")
            lines.append("")

            if tip.get("verification_notes"):
                lines.append(f"**Verification:** {tip.get('verification_notes')}")
                lines.append("")

            if ts:
                warning = _format_timestamp_warning(video_seconds, video_duration)
                if warning:
                    lines.append(warning)
                    lines.append("")

            lines.append("---")
            lines.append("")
    else:
        lines.append("## Final Verified Tips")
        lines.append("")
        lines.append("*No tips passed verification*")
        lines.append("")

    # Removed tips
    removed_tips = metadata.get("removed_tips", []) if metadata else []
    if removed_tips:
        lines.append("## Removed Tips (confidence < 8)")
        lines.append("")
        lines.append("| ID | Reason | Confidence |")
        lines.append("|----|--------|------------|")
        for tip in removed_tips:
            lines.append(f"| {tip.get('id', '?')} | {tip.get('reason', '?')} | {tip.get('confidence', '?')} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Raw Analyst output (if available)
    analyst_out = metadata.get("analyst_output", {}) if metadata else {}
    if analyst_out and analyst_out.get("tips"):
        lines.append("## Raw Analyst Output (before verification)")
        lines.append("")
        lines.extend(_format_analyst_output(analyst_out, video_duration))

    return lines


async def run_single_analysis(
    video_file,
    demo_data: dict,
    game_type: str,
    agent: Optional[str],
    client
) -> dict:
    """
    Run a single analysis (either individual agent or full pipeline).

    Args:
        video_file: Gemini video file object (already uploaded)
        demo_data: Parsed demo data
        game_type: 'cs2' for Counter-Strike 2
        agent: Agent name ('analyst') or None for full pipeline
        client: Gemini client

    Returns:
        Analysis result as dict
    """
    from services.agents.orchestrator import PipelineOrchestrator

    orchestrator = PipelineOrchestrator(
        video_file=video_file,
        replay_data=demo_data,
        game_type=game_type,
        knowledge_base="",
    )

    if agent == "analyst":
        output = await orchestrator.run_analyst_only()
    else:
        output = await orchestrator.analyze()

    return output.model_dump()


async def process_video(
    test_case: VideoTestCase,
    agents_to_run: list[Optional[str]],
    delay_seconds: int,
    pov_player: str,
    dry_run: bool = False
) -> dict[str, dict]:
    """
    Process a single video with all requested analyses.

    Uploads video once and reuses for all analyses.

    Args:
        test_case: Video test case to process
        agents_to_run: List of agents to run (None = full pipeline)
        delay_seconds: Delay between API calls
        pov_player: Name of the POV player (for death timeline)
        dry_run: If True, skip actual analysis

    Returns:
        Dict mapping agent name to results
    """
    from services.agents.base import get_gemini_client, upload_video_to_gemini
    from test_pipeline import parse_replay

    results = {}

    if dry_run:
        for agent in agents_to_run:
            agent_name = agent or "full"
            results[agent_name] = {"dry_run": True}
        return results

    # Parse demo once
    logger.info(f"Parsing demo: {test_case.demo_path.name}")
    demo_data = parse_replay(test_case.demo_path, "cs2")

    # Set POV player - this is critical for accurate analysis
    demo_data["pov_player"] = pov_player
    logger.info(f"POV player set to: {demo_data['pov_player']}")

    # Initialize client and upload video once
    logger.info(f"Uploading video: {test_case.video_path.name}")
    client = get_gemini_client()
    video_file = await upload_video_to_gemini(client, str(test_case.video_path))
    logger.info(f"Video uploaded: {video_file.name}")

    try:
        for i, agent in enumerate(agents_to_run):
            agent_name = agent or "full"
            logger.info(f"Running {agent_name} analysis for {test_case.video_name}")

            start_time = time.time()
            try:
                result = await run_single_analysis(
                    video_file=video_file,
                    demo_data=demo_data,
                    game_type="cs2",
                    agent=agent,
                    client=client
                )
                elapsed = time.time() - start_time

                # Validate timestamps
                warnings = validate_timestamps(
                    result,
                    test_case.duration_seconds or 0,
                    agent
                )

                # Format and save markdown
                markdown = format_as_markdown(
                    result=result,
                    agent=agent,
                    video_name=test_case.video_name,
                    video_duration=test_case.duration_seconds,
                    elapsed_seconds=elapsed,
                    timestamp_warnings=warnings
                )

                # Save markdown file
                output_filename = f"{test_case.video_name}_analysis_{agent_name}.md"
                output_path = test_case.video_path.parent / output_filename
                output_path.write_text(markdown)
                logger.info(f"Saved: {output_filename}")

                # Also save raw JSON
                json_filename = f"{test_case.video_name}_analysis_{agent_name}.json"
                json_path = test_case.video_path.parent / json_filename
                with open(json_path, "w") as f:
                    json.dump(result, f, indent=2, default=str)
                logger.info(f"Saved: {json_filename}")

                results[agent_name] = {
                    "success": True,
                    "elapsed_seconds": elapsed,
                    "output_file": str(output_path),
                    "json_file": str(json_path),
                    "timestamp_warnings": warnings,
                    "tips_count": len(result.get("tips", []))
                }

            except Exception as e:
                logger.error(f"Error running {agent_name}: {e}")
                import traceback
                traceback.print_exc()
                results[agent_name] = {
                    "success": False,
                    "error": str(e)
                }

            # Rate limit delay (skip after last analysis)
            if i < len(agents_to_run) - 1:
                logger.info(f"Waiting {delay_seconds}s before next analysis (rate limiting)...")
                await asyncio.sleep(delay_seconds)

    finally:
        # Cleanup video file
        logger.info(f"Cleaning up video file: {video_file.name}")
        try:
            client.files.delete(name=video_file.name)
        except Exception as e:
            logger.warning(f"Failed to delete video file: {e}")

    return results


async def main():
    parser = argparse.ArgumentParser(
        description="Batch test CS2 video analysis with the Gemini Agent Pipeline"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=DEFAULT_BASE_PATH,
        help=f"Base path to test video folders (default: {DEFAULT_BASE_PATH})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List videos without running analyses"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=75,
        help="Delay in seconds between API calls (default: 75)"
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=AGENTS,
        default=["full"],
        help="Agents to run (default: full pipeline only)"
    )
    parser.add_argument(
        "--video-filter",
        type=str,
        help="Only process videos matching this substring"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--pov-player",
        type=str,
        default="lucasdemoreno",
        help="Name of the POV player in the videos (default: lucasdemoreno)"
    )

    args = parser.parse_args()

    # Update log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Validate base path
    if not args.base_path.exists():
        print(f"Error: Base path does not exist: {args.base_path}", file=sys.stderr)
        sys.exit(1)

    # Discover videos
    print(f"\nDiscovering CS2 test videos in: {args.base_path}")
    print("=" * 60)

    test_cases = discover_videos(args.base_path)

    if not test_cases:
        print("No test videos found!", file=sys.stderr)
        sys.exit(1)

    # Apply video filter if specified
    if args.video_filter:
        test_cases = [tc for tc in test_cases if args.video_filter in tc.video_name]
        if not test_cases:
            print(f"No videos match filter: {args.video_filter}", file=sys.stderr)
            sys.exit(1)

    # Convert agent list (replace "full" with None)
    agents_to_run = [None if a == "full" else a for a in args.agents]

    # Calculate totals
    total_videos = len(test_cases)
    total_analyses = total_videos * len(agents_to_run)
    estimated_time_mins = (total_analyses * (args.delay + 120)) / 60  # 120s estimated per analysis

    print(f"\nTest Summary:")
    print(f"  Videos: {total_videos}")
    print(f"  Analyses per video: {len(agents_to_run)}")
    print(f"  Total analyses: {total_analyses}")
    if not args.dry_run:
        print(f"  Delay between calls: {args.delay}s")
        print(f"  Estimated runtime: ~{estimated_time_mins:.0f} minutes")

    print(f"\nVideos to process:")
    for tc in test_cases:
        duration_str = f" ({tc.duration_seconds:.0f}s)" if tc.duration_seconds else ""
        print(f"  - {tc.video_name}{duration_str}")
        print(f"    Demo: {tc.demo_path.name}")

    print(f"\nAgents to run: {', '.join(a or 'full' for a in agents_to_run)}")
    print(f"POV player: {args.pov_player}")

    if args.dry_run:
        print("\n[DRY RUN] No analyses will be executed.")
        return

    print("\n" + "=" * 60)
    print("Starting batch analysis (2-agent architecture)...")
    print("=" * 60)

    start_time = time.time()
    all_results = {}
    successful = 0
    failed = 0

    for i, test_case in enumerate(test_cases):
        print(f"\n[{i+1}/{total_videos}] Processing: {test_case.video_name}")
        print("-" * 40)

        results = await process_video(
            test_case=test_case,
            agents_to_run=agents_to_run,
            delay_seconds=args.delay,
            pov_player=args.pov_player,
            dry_run=args.dry_run
        )

        all_results[test_case.video_name] = results

        # Count successes/failures
        for agent_name, result in results.items():
            if result.get("success"):
                successful += 1
            else:
                failed += 1

        # Delay between videos (rate limiting for upload)
        if i < len(test_cases) - 1:
            logger.info(f"Waiting {args.delay}s before next video...")
            await asyncio.sleep(args.delay)

    # Final summary
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("BATCH ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nTotal time: {total_time / 60:.1f} minutes")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    # List output files
    print("\nGenerated files:")
    for video_name, results in all_results.items():
        for agent_name, result in results.items():
            if result.get("success"):
                print(f"  {result.get('output_file')}")
                print(f"    Tips: {result.get('tips_count', '?')}")
                if result.get("timestamp_warnings"):
                    print(f"    WARNINGS: {len(result['timestamp_warnings'])} timestamp issues")

    # Save summary JSON
    summary_path = args.base_path / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_time_seconds": total_time,
            "successful": successful,
            "failed": failed,
            "results": all_results
        }, f, indent=2, default=str)
    print(f"\nSummary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
