# Forging 🔥

AI-powered game analysis for esports improvement. Upload your replay files and get personalized coaching feedback powered by Gemini AI.

## Supported Games

- **Age of Empires II: Definitive Edition** - `.aoe2record` files
- **Counter-Strike 2** - `.dem` demo files

## Features

- 📁 Upload replay files for instant AI analysis
- 🎥 Optional video upload for enhanced multimodal analysis
- 🎯 Game-specific coaching feedback
- 📊 Build order analysis, timing comparisons, and improvement suggestions
- ⚡ Fast parsing with battle-tested libraries (mgz, demoparser2)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                              Deploy: Cloud Run      │
│  • File upload UI                                                       │
│  • Analysis results display                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Backend (Python FastAPI)                        Deploy: Cloud Run      │
│  • Replay parsing (mgz, demoparser2)                                    │
│  • Gemini AI integration                                                │
│  • GCS signed URLs for video upload                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│  Google Cloud Storage    │              │  Gemini API              │
│  • Video uploads         │──────────────│  • Multimodal analysis   │
│  • Auto-cleanup (24h)    │              │  • Coaching feedback     │
└──────────────────────────┘              └──────────────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm
- Google Cloud account (for deployment)

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
```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_BUCKET_NAME=forging-uploads
ALLOWED_ORIGINS=http://localhost:3000
```

#### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## Deployment

### Google Cloud Setup

1. **Create a Google Cloud project**
   ```bash
   gcloud projects create forging-app
   gcloud config set project forging-app
   ```

2. **Enable required APIs**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

3. **Set up GCS bucket**
   ```bash
   ./scripts/setup-gcs.sh
   ```

4. **Deploy backend**
   ```bash
   ./scripts/deploy-backend.sh
   ```

5. **Deploy frontend to Cloud Run**
   ```bash
   cd frontend
   gcloud run deploy forging-frontend \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Python, FastAPI, uvicorn
- **AI**: Google Gemini API
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
│   │   └── components/    # React components
│   └── package.json
├── backend/                # Python FastAPI application
│   ├── main.py            # API entry point
│   ├── services/          # Business logic
│   │   ├── aoe2_parser.py
│   │   ├── cs2_parser.py
│   │   ├── analyzer.py
│   │   └── storage.py
│   └── requirements.txt
├── scripts/               # Deployment scripts
└── deploy/                # Cloud Run configs
```

## License

MIT

---

Built for the [Gemini 3 Hackathon](https://gemini3.devpost.com/) 🚀
