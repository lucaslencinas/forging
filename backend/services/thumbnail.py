"""
Thumbnail generation service for video analysis.
Extracts frames from videos using ffmpeg.
"""
import logging
import os
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def parse_timestamp_to_seconds(timestamp: str) -> int:
    """
    Parse timestamp string to seconds.

    Supports formats:
    - "1:23" -> 83 seconds
    - "01:23" -> 83 seconds
    - "1:23:45" -> 5025 seconds
    - "90" -> 90 seconds (already seconds)
    """
    try:
        parts = timestamp.strip().split(":")
        if len(parts) == 1:
            return int(parts[0])
        elif len(parts) == 2:
            minutes, seconds = int(parts[0]), int(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 30  # fallback
    except (ValueError, AttributeError):
        return 30  # fallback


def extract_thumbnail(
    video_path: str,
    timestamp_seconds: int = 30,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Extract a single frame from video at given timestamp.

    Args:
        video_path: Path to the video file
        timestamp_seconds: Time offset in seconds to extract frame
        output_path: Optional output path. If None, creates temp file.

    Returns:
        Path to generated thumbnail, or None if extraction failed
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".jpg")

    try:
        # ffmpeg command to extract single frame
        # -ss before -i for fast seeking
        #
        # Key: Use scale with iw*sar to respect display aspect ratio (DAR).
        # Videos may have non-square pixels (SAR != 1:1), meaning the stored
        # resolution differs from the display resolution. For example, a video
        # stored at 1280x720 with DAR 43:18 should display at ~1720x720.
        #
        # The filter chain:
        # 1. scale=iw*sar:ih - Apply SAR to get correct display dimensions
        # 2. setsar=1 - Reset SAR to 1:1 (square pixels) for the output
        # 3. scale=1280:-2 - Scale to max 1280 width, auto height (even number)
        scale_filter = (
            "scale=iw*sar:ih,"  # Apply SAR to pixel dimensions
            "setsar=1,"  # Reset to square pixels
            "scale='min(1280,iw)':-2"  # Scale down if needed, keep aspect ratio
        )
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp_seconds),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",  # High quality JPEG (1-31, lower is better)
            "-vf", scale_filter,
            "-y",  # Overwrite output file
            output_path
        ]

        logger.info(f"Extracting thumbnail at {timestamp_seconds}s from {video_path}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg failed: {result.stderr}")
            return None

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Thumbnail extracted: {output_path}")
            return output_path
        else:
            logger.error("Thumbnail file not created or empty")
            return None

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out")
        return None
    except FileNotFoundError:
        logger.error("ffmpeg not found - ensure it's installed")
        return None
    except Exception as e:
        logger.error(f"Thumbnail extraction failed: {e}")
        return None


def extract_thumbnail_from_first_tip(
    video_path: str,
    tips: list,
    output_path: Optional[str] = None
) -> Optional[str]:
    """
    Extract thumbnail at the timestamp of the first coaching tip.

    Args:
        video_path: Path to the video file
        tips: List of tips with 'timestamp' field (e.g., "1:23")
        output_path: Optional output path

    Returns:
        Path to generated thumbnail, or None if extraction failed
    """
    timestamp_seconds = 30  # default fallback

    if tips and len(tips) > 0:
        first_tip = tips[0]
        if isinstance(first_tip, dict) and "timestamp" in first_tip:
            timestamp_seconds = parse_timestamp_to_seconds(first_tip["timestamp"])
        elif hasattr(first_tip, "timestamp"):
            timestamp_seconds = parse_timestamp_to_seconds(first_tip.timestamp)

    logger.info(f"Using timestamp {timestamp_seconds}s for thumbnail (from first tip)")
    return extract_thumbnail(video_path, timestamp_seconds, output_path)
