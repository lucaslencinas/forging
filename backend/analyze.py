#!/usr/bin/env python3
"""
CLI tool for analyzing game replays.

Usage:
    python analyze.py replay.aoe2record
    python analyze.py replay.aoe2record --provider claude
    python analyze.py demo.dem --provider openai --model gpt-4o-mini
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from services.aoe2_parser import parse_aoe2_replay
from services.cs2_parser import parse_cs2_demo
from services.analyzer import analyze_game, AnalysisResult
from services.llm import get_available_providers


def detect_game_type(file_path: Path) -> str:
    """Detect game type from file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".aoe2record":
        return "aoe2"
    elif suffix == ".dem":
        return "cs2"
    else:
        raise ValueError(f"Unknown file type: {suffix}. Supported: .aoe2record, .dem")


def parse_replay(file_path: Path, game_type: str) -> dict:
    """Parse replay file based on game type."""
    if game_type == "aoe2":
        return parse_aoe2_replay(str(file_path))
    elif game_type == "cs2":
        return parse_cs2_demo(str(file_path))
    else:
        raise ValueError(f"Unknown game type: {game_type}")


def print_result(result: AnalysisResult):
    """Print analysis result to console."""
    if result.error:
        print(f"\nError: {result.error}", file=sys.stderr)
        return

    print(f"\n{'='*60}")
    print(f"Analysis by {result.provider} ({result.model})")
    print(f"{'='*60}\n")

    print("Tips to improve:\n")
    for i, tip in enumerate(result.tips, 1):
        print(f"  {i}. {tip}\n")

    if "--verbose" in sys.argv or "-v" in sys.argv:
        print(f"\n{'='*60}")
        print("Raw response:")
        print(f"{'='*60}\n")
        print(result.raw_response)


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze game replays with AI coaching"
    )
    parser.add_argument(
        "replay_file",
        type=Path,
        nargs="?",
        help="Path to replay file (.aoe2record or .dem)"
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["gemini", "claude", "openai"],
        help="LLM provider to use (auto-selects if not specified)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Specific model to use"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show raw LLM response"
    )
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available LLM providers and exit"
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Only parse the replay, don't analyze with LLM"
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

    # List providers mode
    if args.list_providers:
        available = get_available_providers()
        print("Available LLM providers:")
        for p in available:
            print(f"  - {p}")
        if not available:
            print("  (none configured)")
            print("\nSet one of: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY")
        return

    # Validate input file
    if not args.replay_file:
        print("Error: replay_file is required", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not args.replay_file.exists():
        print(f"Error: File not found: {args.replay_file}", file=sys.stderr)
        sys.exit(1)

    # Detect game type
    try:
        game_type = detect_game_type(args.replay_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {game_type.upper()} replay: {args.replay_file}")

    # Parse replay
    try:
        game_data = parse_replay(args.replay_file, game_type)
    except Exception as e:
        print(f"Error parsing replay: {e}", file=sys.stderr)
        sys.exit(1)

    # Print summary
    summary = game_data.get("summary", {})
    players = summary.get("players", [])

    print(f"\nGame Summary:")
    print(f"  Map: {summary.get('map', 'Unknown')}")
    print(f"  Duration: {summary.get('duration_seconds', 0) // 60} minutes")
    print(f"  Players:")
    for p in players:
        status = "W" if p.get("winner") else "L"
        print(f"    [{status}] {p.get('name')} ({p.get('civilization')})")

    # Parse-only mode
    if args.parse_only:
        if args.verbose:
            import json
            print(f"\n{'='*60}")
            print("Full parsed data:")
            print(f"{'='*60}")
            # Don't print raw data, it's too big
            data_to_print = {k: v for k, v in game_data.items() if k != "raw"}
            print(json.dumps(data_to_print, indent=2, default=str))
        return

    # Analyze with LLM
    print(f"\nAnalyzing with AI...")
    result = await analyze_game(
        game_type=game_type,
        game_data=game_data,
        provider_name=args.provider,
        model=args.model
    )

    print_result(result)


if __name__ == "__main__":
    asyncio.run(main())
