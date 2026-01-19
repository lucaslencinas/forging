"""
Text-to-Speech service using Gemini 2.5 Flash TTS.

Generates audio narration for coaching tips using Gemini's native TTS model.
"""
import logging
import os
import tempfile
import time
from typing import Optional

from google import genai
from google.genai import types

from services.gcs import upload_file

logger = logging.getLogger(__name__)

# Cache the Gemini client
_genai_client = None

# TTS Model and Voice configuration
TTS_MODEL = "gemini-2.5-flash-preview-tts"
TTS_VOICE = "Charon"  # Informative coaching voice

# Rate limiting settings
TTS_DELAY_SECONDS = 1.0  # Delay between TTS calls to avoid rate limits
TTS_RETRY_DELAY_SECONDS = 20.0  # Delay before retry on rate limit error
TTS_MAX_RETRIES = 2


def _get_api_key() -> str:
    """Get Gemini API key for TTS, with priority for dedicated TTS key."""
    # Priority 1: Dedicated TTS key (for paid tier with higher rate limits)
    tts_key = os.environ.get("GEMINI_TTS_API_KEY", "")
    if tts_key:
        logger.debug("Using dedicated GEMINI_TTS_API_KEY")
        return tts_key

    # Priority 2: First key from comma-separated keys
    api_keys_str = os.environ.get("GEMINI_API_KEYS", "")
    if api_keys_str:
        keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
        if keys:
            logger.debug("Using first key from GEMINI_API_KEYS")
            return keys[0]

    # Priority 3: Single key fallback
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        logger.debug("Using GEMINI_API_KEY")
        return api_key

    raise ValueError("No Gemini API key found. Set GEMINI_TTS_API_KEY, GEMINI_API_KEYS, or GEMINI_API_KEY")


def _get_genai_client() -> genai.Client:
    """Get Gemini client with API key."""
    global _genai_client
    if _genai_client is None:
        api_key = _get_api_key()
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def _reset_client():
    """Reset the cached client (useful if API key changes)."""
    global _genai_client
    _genai_client = None


def generate_tip_audio(tip_text: str, retries: int = TTS_MAX_RETRIES) -> bytes:
    """
    Generate audio for a single tip using Gemini TTS.

    Args:
        tip_text: The coaching tip text to convert to speech
        retries: Number of retries on rate limit errors

    Returns:
        Raw PCM audio content as bytes
    """
    client = _get_genai_client()

    # Add coaching context to the prompt for better delivery
    prompt = f"Read this coaching tip in an informative, helpful tone: {tip_text}"

    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=TTS_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=TTS_VOICE,
                            )
                        )
                    ),
                )
            )

            # Extract audio data from the response
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            return audio_data

        except Exception as e:
            error_str = str(e).lower()
            is_rate_limit = "rate" in error_str or "quota" in error_str or "429" in error_str

            if is_rate_limit and attempt < retries:
                logger.warning(f"TTS rate limit hit, waiting {TTS_RETRY_DELAY_SECONDS}s before retry {attempt + 1}/{retries}")
                time.sleep(TTS_RETRY_DELAY_SECONDS)
                continue
            else:
                raise


def _convert_wav_to_mp3(wav_data: bytes) -> bytes:
    """Convert WAV audio data to MP3 using ffmpeg."""
    import subprocess

    # Write WAV to temp file
    fd_in, temp_wav = tempfile.mkstemp(suffix=".wav")
    fd_out, temp_mp3 = tempfile.mkstemp(suffix=".mp3")

    try:
        os.write(fd_in, wav_data)
        os.close(fd_in)
        os.close(fd_out)

        # Convert using ffmpeg
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "s16le",  # Raw PCM format
                "-ar", "24000",  # Sample rate from Gemini
                "-ac", "1",  # Mono
                "-i", temp_wav,
                "-codec:a", "libmp3lame",
                "-qscale:a", "2",  # High quality
                temp_mp3
            ],
            capture_output=True,
            check=True
        )

        with open(temp_mp3, "rb") as f:
            return f.read()

    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)


def generate_tips_audio(tips: list[dict], analysis_id: str) -> list[str]:
    """
    Generate TTS audio for all tips and upload to GCS.

    Args:
        tips: List of tip dictionaries with "tip" key containing the text
        analysis_id: The analysis ID for GCS path organization

    Returns:
        List of GCS object names for the audio files
    """
    if not tips:
        return []

    audio_object_names = []
    logger.info(f"Generating Gemini TTS audio for {len(tips)} tips")

    for i, tip in enumerate(tips):
        try:
            tip_text = tip.get("tip", "")
            if not tip_text:
                logger.warning(f"Tip {i} has no text, skipping")
                continue

            # Rate limiting: wait between calls to avoid hitting limits
            if i > 0:
                logger.debug(f"Waiting {TTS_DELAY_SECONDS}s before next TTS call")
                time.sleep(TTS_DELAY_SECONDS)

            # Generate audio using Gemini TTS
            wav_audio = generate_tip_audio(tip_text)

            # Convert to MP3 for smaller file size
            try:
                audio_content = _convert_wav_to_mp3(wav_audio)
                content_type = "audio/mpeg"
                file_ext = "mp3"
            except Exception as e:
                logger.warning(f"MP3 conversion failed, using WAV: {e}")
                audio_content = wav_audio
                content_type = "audio/wav"
                file_ext = "wav"

            # Save to temp file
            fd, temp_path = tempfile.mkstemp(suffix=f".{file_ext}")
            try:
                os.write(fd, audio_content)
                os.close(fd)

                # Upload to GCS
                object_name = f"audio/{analysis_id}/tip_{i}.{file_ext}"
                upload_file(temp_path, object_name, content_type=content_type)
                audio_object_names.append(object_name)
                logger.info(f"Generated audio for tip {i}: {object_name}")

            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Failed to generate audio for tip {i}: {e}")
            # Continue with other tips - partial audio is better than none

    logger.info(f"Generated {len(audio_object_names)} audio files using Gemini TTS")
    return audio_object_names
