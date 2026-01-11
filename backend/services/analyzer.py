"""
Game analysis service using LLM providers.
"""
import logging
from typing import Any, Optional
from dataclasses import dataclass

from services.llm import get_llm_provider, get_available_providers, LLMResponse
from services.aoe2_parser import format_for_gemini as format_aoe2
from services.cs2_parser import format_for_gemini as format_cs2

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of game analysis."""
    tips: list[str]
    raw_response: str
    model: str
    provider: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "tips": self.tips,
            "raw_response": self.raw_response,
            "model": self.model,
            "provider": self.provider,
            "error": self.error
        }


# Simplified prompts focused on 3-5 actionable tips
AOE2_SYSTEM_PROMPT = """You are an Age of Empires II coach. Analyze the game data and provide exactly 3-5 specific, actionable tips to improve.

Focus on:
- Build order efficiency and age-up times
- Economy mistakes (idle TC, villager distribution)
- Military decisions and unit composition
- Key moments that decided the game

Be concise. Each tip should be 1-2 sentences max."""

CS2_SYSTEM_PROMPT = """You are a Counter-Strike 2 coach. Analyze the game data and provide exactly 3-5 specific, actionable tips to improve.

Focus on:
- Aim and crosshair placement
- Positioning mistakes
- Economy decisions
- Utility usage

Be concise. Each tip should be 1-2 sentences max."""


def get_system_prompt(game_type: str) -> str:
    """Get the system prompt for a game type."""
    if game_type == "aoe2":
        return AOE2_SYSTEM_PROMPT
    elif game_type == "cs2":
        return CS2_SYSTEM_PROMPT
    else:
        raise ValueError(f"Unknown game type: {game_type}")


def format_game_data(game_type: str, game_data: dict) -> str:
    """Format game data for LLM analysis."""
    if game_type == "aoe2":
        return format_aoe2(game_data)
    elif game_type == "cs2":
        return format_cs2(game_data)
    else:
        raise ValueError(f"Unknown game type: {game_type}")


def parse_tips_from_response(text: str) -> list[str]:
    """Extract tips from LLM response."""
    tips = []
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Match numbered items (1. or 1) or bullet points (- or *)
        if len(line) > 2 and (
            (line[0].isdigit() and line[1] in ".)")
            or line.startswith("- ")
            or line.startswith("* ")
        ):
            # Remove the prefix
            if line[0].isdigit():
                tip = line[2:].strip()
            else:
                tip = line[2:].strip()

            # Remove markdown bold if present
            if tip.startswith("**") and "**" in tip[2:]:
                # Extract text, removing bold markers
                tip = tip.replace("**", "")

            if tip:
                tips.append(tip)

    # If we couldn't parse structured tips, just return the whole response split
    if not tips and text.strip():
        # Return the response as a single tip if parsing failed
        tips = [text.strip()[:500]]

    return tips[:5]  # Max 5 tips


async def analyze_game(
    game_type: str,
    game_data: dict[str, Any],
    provider_name: Optional[str] = None,
    model: Optional[str] = None
) -> AnalysisResult:
    """
    Analyze a game and return tips for improvement.

    Args:
        game_type: "aoe2" or "cs2"
        game_data: Parsed game data from the respective parser
        provider_name: LLM provider to use (gemini, claude, openai). Auto-selects if None.
        model: Specific model to use. Uses provider default if None.

    Returns:
        AnalysisResult with tips and metadata
    """
    # Get the LLM provider
    provider = get_llm_provider(provider_name, model)

    if not provider.is_available():
        available = get_available_providers()
        return AnalysisResult(
            tips=[],
            raw_response="",
            model="none",
            provider=provider.name,
            error=f"No LLM provider available. Configure one of: GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY. Available: {available}"
        )

    # Format the data and prompts
    system_prompt = get_system_prompt(game_type)
    formatted_data = format_game_data(game_type, game_data)

    user_prompt = f"""Analyze this {game_type.upper()} game and provide 3-5 specific tips to improve:

{formatted_data}

Reply with a numbered list of 3-5 tips. Be specific and actionable."""

    # Generate response
    logger.info(f"Analyzing {game_type} game with {provider.name}")
    response = await provider.generate(user_prompt, system_prompt)

    if not response.success:
        return AnalysisResult(
            tips=[],
            raw_response="",
            model=response.model,
            provider=response.provider,
            error=response.error
        )

    # Parse tips from response
    tips = parse_tips_from_response(response.content)

    return AnalysisResult(
        tips=tips,
        raw_response=response.content,
        model=response.model,
        provider=response.provider
    )


# Keep old function signature for backwards compatibility with webapp
async def analyze_with_gemini(
    game_type: str,
    game_data: dict[str, Any],
    video_gcs_uri: Optional[str] = None  # Ignored for now
) -> dict[str, Any]:
    """
    Legacy wrapper for webapp compatibility.
    """
    result = await analyze_game(game_type, game_data)
    return {
        "tips": result.tips,
        "raw_analysis": result.raw_response,
        "model_used": result.model,
        "provider": result.provider,
        "error": result.error
    }


def list_available_models():
    """Log available LLM providers at startup."""
    available = get_available_providers()
    if available:
        logger.info(f"Available LLM providers: {available}")
    else:
        logger.warning("No LLM providers configured")
