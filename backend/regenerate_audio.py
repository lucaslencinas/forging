#!/usr/bin/env python3
"""
CLI tool to regenerate TTS audio for an existing analysis.

Usage:
    python regenerate_audio.py <analysis_id>

Example:
    python regenerate_audio.py 25371c3c
"""
import argparse
import asyncio
import logging
import sys

from dotenv import load_dotenv

# Load environment variables before other imports
load_dotenv()

from services.firestore import get_analysis, update_analysis
from services.tts import generate_tips_audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def regenerate_audio(analysis_id: str) -> bool:
    """
    Regenerate TTS audio for an analysis.

    Args:
        analysis_id: The analysis ID to regenerate audio for

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Fetching analysis {analysis_id} from Firestore...")

    # Get the analysis from Firestore
    analysis = await get_analysis(analysis_id)
    if not analysis:
        logger.error(f"Analysis {analysis_id} not found")
        return False

    # Extract tips
    tips = analysis.get("tips", [])
    if not tips:
        logger.error(f"Analysis {analysis_id} has no tips")
        return False

    logger.info(f"Found {len(tips)} tips to regenerate audio for")

    # Show tip previews
    for i, tip in enumerate(tips):
        tip_text = tip.get("tip", "")[:80]
        logger.info(f"  Tip {i}: {tip_text}...")

    # Generate audio
    logger.info("Generating TTS audio (this may take a while)...")
    tips_for_tts = [{"tip": tip.get("tip", "")} for tip in tips]
    audio_object_names = generate_tips_audio(tips_for_tts, analysis_id)

    if not audio_object_names:
        logger.error("Failed to generate any audio files")
        return False

    logger.info(f"Generated {len(audio_object_names)} audio files:")
    for name in audio_object_names:
        logger.info(f"  - {name}")

    # Update Firestore with new audio URLs
    logger.info("Updating Firestore with new audio URLs...")
    await update_analysis(analysis_id, {"audio_urls": audio_object_names})

    logger.info(f"Successfully regenerated audio for analysis {analysis_id}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate TTS audio for an existing analysis"
    )
    parser.add_argument(
        "analysis_id",
        help="The analysis ID to regenerate audio for"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    success = asyncio.run(regenerate_audio(args.analysis_id))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
