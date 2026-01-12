# Repository README Updates

The public GitHub README needs to be polished for judges. Here's what to update:

---

## Current README Issues to Fix

- [ ] Update "Current Status" section to reflect submission state
- [ ] Add clear setup instructions that actually work
- [ ] Add screenshots/GIF of the app in action
- [ ] Add the demo video link once recorded
- [ ] Add "Built for Gemini API Developer Competition" badge/section

---

## Suggested README Structure

```markdown
# Forging

**AI-powered coaching for Age of Empires II** - Get pro-level game analysis without the pro-level price tag.

Built with Gemini 3 for the [Gemini API Developer Competition](link).

[Screenshot or GIF of the app here]

## What it does

Upload a recording of your AoE2 game, and Forging analyzes it like a human coach:
- Game summary with key moments
- Timestamped mistakes with specific feedback
- Prioritized improvement suggestions
- Resource management and timing analysis

## Demo

[Link to 3-minute demo video]

[Link to live app]

## How it works

1. **Upload** - Drop your gameplay recording (MP4)
2. **Analyze** - Gemini 3 watches the game using multimodal video understanding
3. **Improve** - Get actionable coaching feedback with timestamps

## Gemini 3 Features Used

- **Multimodal video understanding** - Analyzes gameplay frames to understand game state
- **Long context window** - Processes entire 30+ minute games
- **Structured output** - Returns consistent JSON for the coaching UI

## Tech Stack

- **Backend**: Python, FastAPI, Gemini 3 API
- **Frontend**: Next.js, React, TypeScript
- **Infrastructure**: Google Cloud Run, Google Cloud Storage

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Gemini API key

### Backend Setup

\`\`\`bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
python main.py
\`\`\`

### Frontend Setup

\`\`\`bash
cd frontend
pnpm install
pnpm dev
\`\`\`

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Gemini API key |
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket for uploads |
| `GEMINI_ENABLED` | Set to `true` to enable Gemini |

## Architecture

[Include the architecture diagram from the existing README]

## License

MIT

---

Built for the Gemini API Developer Competition 2025
```

---

## Screenshots to Add

Capture these screenshots for the README:

1. [ ] **Landing page** - Clean shot of the upload interface
2. [ ] **Upload in progress** - Shows the progress bar
3. [ ] **Analysis results** - Full coaching report view
4. [ ] **Mobile view** - If responsive (optional)

Recommended: Use a GIF showing the full flow (upload → loading → results) - more engaging than static screenshots.

Tools for GIFs:
- macOS: Kap (free)
- Cross-platform: ScreenToGif, LICEcap

---

## Badge to Add

Add near the top of README:

```markdown
[![Gemini API Competition](https://img.shields.io/badge/Gemini%20API-Developer%20Competition%202025-blue)](competition-link)
```

---

## Things to Remove/Hide Before Submission

- [ ] Any TODO comments in the README
- [ ] Development/debug instructions that aren't needed
- [ ] References to "not working yet" features
- [ ] Personal notes or work-in-progress sections
