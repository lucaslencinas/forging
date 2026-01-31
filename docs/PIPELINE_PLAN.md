# Analysis Pipeline

> **Status:** Implemented
> **Created:** 2025-01-21
> **Last Updated:** 2025-01-31

## Overview

2-agent pipeline for video game coaching analysis.

| Agent | Role | Output |
|-------|------|--------|
| **Observer** | Multi-angle gameplay analysis | 10-20 tips with timestamps |
| **Validator** | Verifies tips against video evidence | Verified tips with confidence scores |

---

## Architecture

```
                    +-------------------------------------+
                    |       VIDEO + REPLAY DATA           |
                    +-------------------------------------+
                                       |
                                       v
                    +------------------+
                    | Round Detector   |  (CS2 only - quick call)
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |    OBSERVER      |
                    |                  |
                    |  Multi-Angle     |
                    |  Analysis:       |
                    |                  |
                    |  - Exploitable   |
                    |    Patterns      |
                    |  - Rank-Up       |
                    |    Habits        |
                    |  - Missed        |
                    |    Adaptations   |
                    |                  |
                    |  thinking: HIGH  |
                    +--------+---------+
                             |
                             | 10-20 tips
                             v
                    +------------------+
                    |    VALIDATOR     |
                    |                  |
                    |  2-Step Verify:  |
                    |                  |
                    |  1. Video check  |
                    |     (5s window)  |
                    |  2. POV player   |
                    |     verification |
                    |                  |
                    |  Confidence      |
                    |  scoring 1-10    |
                    |  Keep >= 8       |
                    |                  |
                    |  thinking: HIGH  |
                    +--------+---------+
                             |
                             v
                       Final Output
                    (ProducerOutput with
                     tips + summary_text)
```

**Key features:**
- Simple 2-agent flow
- Explicit confidence scoring
- Clear verification criteria
- Round detection to filter demo data (CS2)

---

## File Structure

```
backend/
├── services/
│   ├── agents/
│   │   ├── __init__.py           # Exports orchestrator
│   │   ├── base.py               # BaseAgent base class
│   │   ├── contracts.py          # Pydantic models for data flow
│   │   ├── analyst.py            # ObserverAgent (multi-angle analysis)
│   │   ├── verifier.py           # ValidatorAgent (verification)
│   │   └── orchestrator.py       # PipelineOrchestrator
│   └── cs2_parser.py             # Demo parser (grenades, bomb, etc.)
│   └── aoe2_parser.py            # Replay parser
```

---

## Agent Details

### Observer

**Role:** Combined multi-angle gameplay analysis.

Analyzes from THREE perspectives:
1. **Exploitable Patterns**: What would an opponent exploit?
2. **Rank-Up Habits**: What recurring habits are holding you back?
3. **Missed Adaptations**: Did you react to what you saw/heard?

**Output:** `AnalystOutput` with `tips[]`
- Each tip has: `timestamp`, `category`, `severity`, `observation`, `why_it_matters`, `fix`, `reasoning`

---

### Validator

**Role:** 2-step verification with confidence scoring.

**Step 1: Video Cross-Check**
- Navigate to timestamp
- Watch 5s before and after
- Verify event happened as described

**Step 2: POV Player Verification**
- Confirm action is by POV player (not teammates)
- Check player was alive at timestamp
- Verify action is visible in video

**Confidence Scoring:**
- 9-10: Clearly visible, timestamp accurate, exactly as described
- 8: Visible, timestamp close, mostly matches
- 5-7: Happened but timestamp off or different player (REMOVE)
- 1-4: Hallucination - didn't happen (REMOVE)

**Output:** `ProducerOutput` with `tips[]`, `summary_text`, `pipeline_metadata`

---

## Testing

```bash
# Test full pipeline
python test_pipeline.py video.mp4 replay.dem

# Test observer only
python test_pipeline.py video.mp4 replay.dem --agent observer

# Use existing Gemini file (skip re-upload)
python test_pipeline.py files/abc123 replay.dem

# Output to JSON
python test_pipeline.py video.mp4 replay.dem --output results.json
```

---

## Gemini Configuration

| Agent | Thinking Level | Uses Video | Include Thoughts |
|-------|---------------|------------|-----------------|
| Observer | HIGH | Yes | No |
| Validator | HIGH | Yes | No |

Model: `gemini-3-pro-preview` (configurable via `PIPELINE_MODEL` env var)

---

## Data Contracts

See `backend/services/agents/contracts.py` for Pydantic models:

- `Timestamp` - Video time with display format
- `AnalystTip` - Observer output
- `AnalystOutput` - Collection of tips from Observer
- `VerifiedTip` - Final tip format with confidence
- `RemovedTip` - Tip that was rejected during verification
- `VerifierOutput` - Validator output
- `ProducerOutput` - Final pipeline output

---

## Success Criteria

- [x] Pipeline produces verified tips
- [x] Observer generates 10-20 tips with reasoning
- [x] Validator verifies and assigns confidence scores
- [x] Only tips with confidence >= 8 are kept
- [x] Summary text generated for TTS
- [x] Total processing time ~2-3 minutes
