# Forging 🔥

AI-powered game analysis for esports improvement. Upload your replay files and get personalized coaching feedback powered by AI.

## Current Status

### What's Working
- ✅ AoE2 replay parsing (`.aoe2record` files)
- ✅ CS2 demo parsing (`.dem` files)
- ✅ LLM analysis with multi-provider support (Gemini, Claude, OpenAI)
- ✅ 3-5 actionable coaching tips per analysis
- ✅ Web UI for uploading and viewing results
- ✅ CLI tool for quick testing (`python analyze.py replay.aoe2record`)
- ✅ Video upload to GCS with progress tracking
- ✅ **Video analysis with timestamped coaching tips** (AoE2 + CS2)
- ✅ **Video player with clickable timestamps**
- ✅ **Gemini 2.5/3.0 model selection** for video analysis
- ✅ Automatic CI/CD deployment via GitHub Actions

### Live Demo

| Service | URL |
|---------|-----|
| Frontend | https://forging-frontend-nht57oxpca-uc.a.run.app |
| Backend API | https://forging-backend-nht57oxpca-uc.a.run.app |

### What's Missing / TODO
- ⬜ User accounts and history
- ⬜ Build order visualization
- ⬜ Comparison with pro player benchmarks
- ✅ ~~Video analysis with timestamped coaching tips~~
- ✅ ~~Video player with clickable timestamps~~
- ✅ ~~Production deployment~~
- ✅ ~~Video upload infrastructure~~

## Supported Games

- **Age of Empires II: Definitive Edition** - `.aoe2record` files
- **Counter-Strike 2** - `.dem` demo files

## Features

- 📁 Upload replay files for instant AI analysis
- 🎥 Video upload with progress tracking (MP4, max 500MB, 15 min)
- 🎬 **Video analysis with AI-powered timestamped coaching tips**
- ⏱️ **Clickable timestamps to jump to specific moments in the video**
- 🎮 **Support for AoE2 and CS2 video analysis**
- 🤖 Multi-provider LLM support (Gemini, Claude, OpenAI) with automatic fallback
- 🎯 Game-specific coaching feedback (3-5 actionable tips)
- 📊 Build order analysis, timing comparisons, and improvement suggestions
- ⚡ Fast parsing with battle-tested libraries (mgz, demoparser2)
- 🖥️ CLI tool for testing and automation
- 🚀 Auto-deploy to Cloud Run via GitHub Actions

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16)                           Deploy: Cloud Run      │
│  • File upload UI                                                       │
│  • Video upload with progress bar                                       │
│  • Video player with clickable timestamps                               │
│  • Analysis results display                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (Python FastAPI)                        Deploy: Cloud Run      │
│  • Replay parsing (mgz, demoparser2)                                    │
│  • Video analysis with Gemini File API                                  │
│  • LLM integration (Gemini/Claude/OpenAI)                               │
│  • GCS signed URL generation                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│  Gemini File API     │ │  LLM Provider    │ │  Google Cloud Storage│
│  • Video upload      │ │  • Gemini 2.5/3  │ │  • Video uploads     │
│  • Multimodal AI     │ │  • Claude        │ │  • Signed URLs       │
│  • Timestamped tips  │ │  • OpenAI        │ │  • 24h auto-delete   │
└──────────────────────┘ └──────────────────┘ └──────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm
- At least one LLM API key (Gemini, Claude, or OpenAI)

### Local Development

1. **Clone the repository**
   ```bash
   git clone git@github-personal:lucaslencinas/forging.git
   cd forging
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Run the backend**
   ```bash
   uvicorn main:app --reload --port 8080
   ```

4. **Set up the frontend** (in a new terminal)
   ```bash
   cd frontend
   pnpm install
   cp .env.example .env.local
   ```

5. **Run the frontend**
   ```bash
   pnpm dev
   ```

6. **Open http://localhost:3000**

### CLI Usage

```bash
cd backend
source venv/bin/activate

# Parse and analyze a replay
python analyze.py path/to/replay.aoe2record

# Use a specific provider
python analyze.py replay.aoe2record --provider claude

# Parse only (no LLM call)
python analyze.py replay.aoe2record --parse-only

# List available providers
python analyze.py --list-providers
```

### Environment Variables

#### Backend (`backend/.env`)
```bash
# LLM API Keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key  # optional
OPENAI_API_KEY=your_openai_api_key        # optional

# Enable/disable providers
GEMINI_ENABLED=true
CLAUDE_ENABLED=true
OPENAI_ENABLED=true

# Server config
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO

# GCS config (for video uploads)
GCS_BUCKET_NAME=forging-uploads
GCS_SIGNING_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com  # optional, for local dev
```

#### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **Backend**: Python 3.12, FastAPI, uvicorn
- **AI**: Gemini, Claude, OpenAI (with automatic fallback)
- **Parsing**:
  - AoE2: [mgz](https://github.com/happyleavesaoc/aoc-mgz)
  - CS2: [demoparser2](https://github.com/LaihoE/demoparser), [awpy](https://github.com/pnxenopoulos/awpy)
- **Cloud**: Google Cloud Run, Google Cloud Storage

## Project Structure

```
forging/
├── frontend/               # Next.js application
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   │   ├── VideoPlayer.tsx        # Video player with seek
│   │   │   ├── TimestampedTips.tsx    # Clickable coaching tips
│   │   │   └── VideoAnalysisResults.tsx
│   │   ├── hooks/         # Custom hooks
│   │   │   └── useVideoUpload.ts      # GCS upload with progress
│   │   └── types/         # Generated API types
│   └── package.json
├── backend/                # Python FastAPI application
│   ├── main.py            # API entry point
│   ├── models.py          # Pydantic models
│   ├── analyze.py         # CLI tool
│   ├── services/
│   │   ├── aoe2_parser.py     # AoE2 replay parsing
│   │   ├── cs2_parser.py      # CS2 demo parsing
│   │   ├── video_analyzer.py  # AoE2 video analysis
│   │   ├── cs2_video_analyzer.py  # CS2 video analysis
│   │   ├── aoe2_knowledge.py  # AoE2 coaching knowledge base
│   │   ├── cs2_knowledge.py   # CS2 coaching knowledge base
│   │   ├── analyzer.py        # LLM analysis orchestration
│   │   ├── gcs.py             # GCS signed URL generation
│   │   └── llm/               # LLM provider abstraction
│   │       ├── base.py        # Abstract provider class
│   │       ├── gemini.py      # Gemini + File API
│   │       ├── claude.py
│   │       ├── openai.py
│   │       └── factory.py     # Provider auto-selection
│   └── requirements.txt
├── .github/workflows/     # CI/CD pipelines
│   ├── deploy-backend.yml
│   └── deploy-frontend.yml
└── deploy/                # GCS CORS config
```

## License

MIT

---

Built for the [Gemini 3 Hackathon](https://gemini3.devpost.com/) 🚀
