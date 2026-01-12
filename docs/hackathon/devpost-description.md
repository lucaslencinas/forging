# Devpost Submission

## Project Name
Forging

## Tagline
AI-powered gaming coach - get pro-level analysis for any competitive game, without the pro-level price tag.

---

## Gemini Integration (~200 words)

Forging leverages Gemini 3's multimodal capabilities to analyze gameplay videos across different game genres - working like a human coach who can watch any game.

**Multimodal Video Understanding**: Gemini 3 watches recorded gameplay frame-by-frame, understanding game state purely from visuals. For an RTS like Age of Empires II, it reads resource bars, unit compositions, and map control. For an FPS like Counter-Strike 2, it analyzes crosshair placement, positioning, and utility usage. No game API required - it sees what a coach sees.

**Long Context Window**: Competitive matches range from 5-minute CS2 rounds to 40-minute AoE2 games. Gemini 3's extended context processes entire matches without chunking, connecting early decisions to late-game outcomes.

**Structured Output**: Analysis returns consistent JSON, enabling a polished UI with timestamped feedback, game summaries, and prioritized improvements. This isn't a chatbot - it's an integrated coaching platform.

The combination makes Forging uniquely possible. Video understanding provides the "eyes" of a coach, long context provides game-length memory, and structured output provides actionable format. The same architecture analyzes completely different genres - proving Gemini 3's multimodal capabilities generalize across visual domains.

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

- **Backend**: Python/FastAPI with game-specific analysis modules
- **Frontend**: Next.js/React with TypeScript for the coaching dashboard
- **Infrastructure**: Google Cloud Run + Cloud Storage for scalable deployment
- **AI**: Gemini 3 API with multimodal video input and structured JSON output

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
- python
- fastapi
- nextjs
- react
- typescript
- google-cloud-run
- google-cloud-storage

## Try it out
[URL to deployed app]

## Links
- [GitHub Repository](https://github.com/...)
- [Demo Video](https://youtube.com/...)
