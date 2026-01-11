# Forging - Project Instructions

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

## Project Structure

- `backend/` - FastAPI Python backend
  - `models.py` - Pydantic models (source of truth for API types)
  - `main.py` - API endpoints
  - `services/` - Game parsers and LLM integration
- `frontend/` - Next.js TypeScript frontend
  - `src/types/api.ts` - Generated types (do not edit manually)
  - `src/components/` - React components
