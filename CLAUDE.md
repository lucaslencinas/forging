# Forging - Project Instructions

## Local Development - GCP Authentication

**IMPORTANT:** The developer uses two gcloud accounts:
- `lucasl@work.com` - Default account (for Claude/Vertex AI, do NOT change)
- `lucasdemoreno93@gmail.com` - Personal account for this project's GCP resources

**Rules for gcloud commands:**
1. NEVER run `gcloud config set account` to change the default
2. ALWAYS use `--account=lucasdemoreno93@gmail.com` when running gcloud commands for this project
3. The backend uses `GCP_LOCAL_ACCOUNT` env var to specify the account for service account impersonation
4. If authentication errors occur locally, run: `gcloud auth login lucasdemoreno93@gmail.com` then immediately restore default: `gcloud config set account lucasl@work.com`

## Git Commits

When creating commits, do NOT include the "Co-Authored-By" line in commit messages.

## Pre-Push Checklist

Before pushing to main, review and update if needed:

1. **README.md** - Update "Current Status" section:
   - Move completed items from "What's Missing" to "What's Working"
   - Add new TODO items as they come up
   - Keep architecture diagram in sync with actual implementation

2. **This file (CLAUDE.md)** - Update if:
   - New patterns or conventions are established
   - New tools or scripts are added
   - Project structure changes significantly

3. **backend/.env.example** - Update if new environment variables are added

## API Type Generation

This project uses OpenAPI codegen to keep TypeScript types in sync with the FastAPI backend.

### When to Regenerate Types

Regenerate TypeScript types whenever you:
- Add or modify Pydantic models in `backend/models.py`
- Change API endpoint response types in `backend/main.py`
- Add new API endpoints

### How to Regenerate Types

```bash
# 1. Start the backend (in one terminal)
cd backend && source venv/bin/activate && python main.py

# 2. Generate types (in another terminal)
cd frontend && pnpm generate-api-types

# 3. Stop the backend (Ctrl+C)
```

This generates `frontend/src/types/api.ts` from the OpenAPI spec at `http://localhost:8080/openapi.json`.

### Type Usage in Frontend

Import types from the generated file:

```typescript
import type { components } from "@/types/api";

type AnalysisResponse = components["schemas"]["AnalysisResponse"];
type Player = components["schemas"]["Player"];
```

## LLM Provider System

The project supports multiple LLM providers with automatic fallback:

- **Gemini** (default) - `GEMINI_API_KEY` + `GEMINI_ENABLED`
- **Claude** - `ANTHROPIC_API_KEY` + `CLAUDE_ENABLED`
- **OpenAI** - `OPENAI_API_KEY` + `OPENAI_ENABLED`

Each provider tries multiple models in order if one fails (e.g., rate limits).

### Adding a New Provider

1. Create `backend/services/llm/newprovider.py` implementing `LLMProvider`
2. Add to `PROVIDERS` dict in `backend/services/llm/factory.py`
3. Add to `DEFAULT_PROVIDER_ORDER` list

## CLI Tool

Quick testing without the web UI:

```bash
cd backend && source venv/bin/activate

# Full analysis
python analyze.py replay.aoe2record

# Parse only (no LLM)
python analyze.py replay.aoe2record --parse-only

# Specific provider
python analyze.py replay.aoe2record --provider claude
```

## Project Structure

- `backend/` - FastAPI Python backend
  - `models.py` - Pydantic models (source of truth for API types)
  - `main.py` - API endpoints
  - `analyze.py` - CLI tool
  - `services/` - Game parsers and LLM integration
    - `llm/` - Provider abstraction layer
- `frontend/` - Next.js TypeScript frontend
  - `src/types/api.ts` - Generated types (do not edit manually)
  - `src/components/` - React components
