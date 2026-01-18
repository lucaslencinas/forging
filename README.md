# Forging 🔥

AI-powered game analysis for esports improvement. Upload your replay files or gameplay videos and get personalized coaching feedback powered by Gemini AI.

## Live Demo

| Service | URL |
|---------|-----|
| Frontend | https://forging-frontend-nht57oxpca-uc.a.run.app |
| Backend API | https://forging-backend-nht57oxpca-uc.a.run.app |

## Features

- 📁 **Replay Analysis** - Upload replay files for instant AI analysis
- 🎥 **Video Coaching** - Upload gameplay recordings (MP4, max 700MB, 30 min) for AI-powered feedback
- ⏱️ **Timestamped Tips** - Clickable timestamps to jump to specific moments in your gameplay
- 🎯 **Personalized Coaching** - 3-5 actionable tips tailored to your gameplay
- 🔗 **Shareable Links** - Share your analysis with teammates or friends
- 🎠 **Community Carousel** - Browse analyses from the community

## Supported Games

- **Age of Empires II: Definitive Edition** - `.aoe2record` replay files and video
- **Counter-Strike 2** - `.dem` demo files and video

## Upcoming Games

- 🚗 **Rocket League** - Car soccer physics analysis
- ⚔️ **Dota 2** - MOBA strategy and team coordination
- 🏆 **League of Legends** - Champion mastery and game sense
- 🌌 **StarCraft II** - RTS build orders and macro management

## What's Next

**MVP Improvements:**
- ⬜ Thumbnail generation for community carousel

**Post-MVP:**
- ⬜ User accounts and analysis history
- ⬜ Build order visualization
- ⬜ Comparison with pro player benchmarks
- ⬜ AI chat with your replay ("Why did I lose that fight?")
- ⬜ Skill progression tracking across multiple games

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
│  • LLM integration (Gemini primary, OpenAI fallback)                    │
│  • GCS signed URL generation                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
┌──────────────────────────────┐ ┌──────────────────────────────────────┐
│  Gemini File API             │ │  Google Cloud                        │
│  • Video upload & analysis   │ │  • Cloud Storage (video uploads)    │
│  • Multimodal AI             │ │  • Firestore (analysis records)     │
│  • Timestamped tips          │ │  • Cloud Run (deployment)           │
└──────────────────────────────┘ └──────────────────────────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS 4
- **Backend**: Python 3.12, FastAPI, uvicorn
- **AI**: Gemini 2.5/3.0 (primary), OpenAI (fallback)
- **Parsing**:
  - AoE2: [mgz](https://github.com/happyleavesaoc/aoc-mgz)
  - CS2: [demoparser2](https://github.com/LaihoE/demoparser), [awpy](https://github.com/pnxenopoulos/awpy)
- **Cloud**: Google Cloud Run, Cloud Storage, Firestore

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm
- Gemini API key (get one at [Google AI Studio](https://aistudio.google.com/))

### Setup

1. **Clone the repository**
   ```bash
   git clone git@github.com:lucaslencinas/forging.git
   cd forging
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
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

### Environment Variables

#### Backend (`backend/.env`)
```bash
# Gemini API (required)
GEMINI_API_KEY=your_gemini_api_key

# Optional: Multiple API keys for rate limit fallback (comma-separated)
# GEMINI_API_KEYS=key1,key2,key3

# Optional: OpenAI as fallback provider
# OPENAI_API_KEY=your_openai_api_key
# OPENAI_ENABLED=true

# Server config
ALLOWED_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO

# GCS config (only needed for video uploads - uses demo mode without it)
# GOOGLE_CLOUD_PROJECT=your-project-id
# GCS_BUCKET_NAME=your-bucket-name
# GCP_LOCAL_ACCOUNT=your-email@gmail.com
```

#### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

### Note for Contributors

The video upload feature requires GCP credentials (Cloud Storage). Without GCP setup:
- **Replay analysis works fully** - Just needs a Gemini API key
- **Video upload is disabled** - Requires GCS bucket access

For hackathon judges: Use the [live demo](https://forging-frontend-nht57oxpca-uc.a.run.app) to test video features, or run locally for replay-only analysis.

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
│   │       ├── openai.py      # OpenAI (fallback)
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
