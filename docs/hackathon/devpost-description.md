# Devpost Submission

## Project Name
Forging

## Tagline
AI-powered gaming coach - get pro-level analysis for any competitive game, without the pro-level price tag.

---

## Gemini Integration (~200 words)

Forging is built as a multi-agent system on top of Gemini 3's Interactions API — not a prompt wrapper.

**2-Agent Pipeline with Interaction Chaining**: An Observer agent analyzes gameplay video with `thinking_level="high"`, generating 10-20 timestamped tips. Its `interaction_id` chains to a Validator agent that cross-checks each tip against the video, assigning confidence scores 1-10. Only tips scoring 8+ survive. The video is uploaded once via the **File API** and persists across the entire chain — no re-upload needed.

**Multimodal Video Understanding**: Gemini 3 Pro watches gameplay frame-by-frame alongside parsed replay data. For CS2, it reads HUD elements, crosshair placement, and positioning. For AoE2, it tracks resources, unit compositions, and build orders. No game API required.

**Structured Output with `response_schema`**: Native JSON schema enforcement ensures deterministic output format at every pipeline step — timestamps, categories, severity, reasoning — directly renderable in the UI.

**Extended Thinking**: Both agents use high thinking levels for deep reasoning. The Observer reasons about gameplay patterns; the Validator reasons about whether each observation is actually visible in the video or a hallucination.

**Follow-up Chat**: Chat chains from the Validator's `interaction_id`, inheriting full pipeline context (video + analysis) without re-sending anything.

---

## Full Description

### Inspiration

Esports has exploded - tournament prize pools exceed $40M, coaching has become a profession, and 500M+ people watch competitive gaming. Yet personalized coaching remains expensive ($50-150/hour) and inaccessible for most players.

I wanted to build the coach every competitive player deserves - one that watches your games, understands your mistakes, and helps you improve. And I wanted to prove it could work across genres, not just one game.

### What it does

Forging analyzes gameplay recordings across different competitive games:

**For Age of Empires II (RTS):**
- Build order analysis and timing feedback
- Resource management tracking ("You floated 2000 gold at 14:32")
- Army composition and engagement analysis

**For Counter-Strike 2 (FPS):**
- Crosshair placement and positioning feedback
- Utility usage analysis
- Economy decision review
- Rotation and timing feedback

Same platform, different games - demonstrating the extensible architecture.

### How I built it

- **Backend**: Python/FastAPI with a 2-agent analysis pipeline (Observer → Validator) using the Gemini Interactions API
- **Frontend**: Next.js/React with TypeScript — video player, timestamped tips, follow-up chat
- **Infrastructure**: Google Cloud Run + Cloud Storage + Firestore
- **AI**: Gemini 3 Pro with Interactions API chaining, extended thinking, structured output (`response_schema`), File API for video, and Gemini 2.5 Flash TTS for voice coaching

### Challenges I ran into

- Designing prompts that work across different visual game languages
- Balancing analysis depth vs. API costs and response time
- Structuring output consistently across game types with different metrics

### Accomplishments that I'm proud of

- **Cross-genre analysis**: Same core platform analyzes both RTS and FPS games
- **Genuinely useful output**: I've used it on my own games in both titles
- **Proof of extensibility**: Adding a new game is prompt configuration, not infrastructure rebuild

### What I learned

- Gemini 3's multimodal capabilities generalize remarkably well across visual domains
- The gap between "one game demo" and "platform" is smaller than expected with good architecture
- Structured output is essential for building real applications vs. chatbot demos

### What's next for Forging

- **More games**: Valorant, League of Legends, Dota 2
- **Trend tracking**: "Your crosshair placement has improved 15% this month"
- **Rank calibration**: Advice tuned to your skill level
- **Team analysis**: Squad-level feedback for team games

**Vision: Full Skill Development Platform**

Inspired by tools like trophi.ai (Rocket League) and Korean esports analytics platforms, we're building toward:

- **Skill Radar Charts**: Visual breakdown of core competencies (Mechanics, Positioning, Game Sense) that evolve over time
- **Graded Metrics**: C+ to S+ scoring on granular skills like APM, map awareness, resource efficiency
- **Personalized Learning Paths**: Rank-specific skill trees ("Gold to Platinum Path") with step-by-step progression
- **Training Recommendations**: Link weaknesses to specific practice drills and workshop maps

The goal: transform from post-game analysis into a complete coaching platform that guides your improvement journey.

---

## Built With
- gemini-3
- gemini-interactions-api
- python
- fastapi
- nextjs
- react
- typescript
- google-cloud-run
- google-cloud-storage
- google-cloud-firestore

## Try it out
[https://forging-frontend-nht57oxpca-uc.a.run.app](https://forging-frontend-nht57oxpca-uc.a.run.app)

## Links
- [GitHub Repository](https://github.com/lucaslencinas/forging)
- Demo Video (link TBD)
