# Forging - Pitch Document

## The Problem

Competitive gamers across all genres hit skill ceilings. To improve beyond intermediate ranks, players traditionally need:

1. **Human coaches** - $30-150/hour depending on the game, scheduling hassles, limited availability
2. **Pro player VOD reviews** - Generic advice, not personalized to your gameplay
3. **Self-review** - Time-consuming, hard to spot your own mistakes, no expert insight

This isn't a niche problem. Esports has exploded into a mainstream industry:

- **$2.1B+ global esports market** (2024), projected to reach $5B+ by 2030
- **Tournament prize pools** have grown 10x in a decade - The International (Dota 2) regularly exceeds $30M
- **Coaching has become professionalized** - Top CS2 coaches earn $20k+/month, and amateur coaching platforms like Metafy and Fiverr have created a thriving marketplace
- **500M+ esports viewers** worldwide, with millions actively playing ranked/competitive modes

Yet accessible, personalized coaching remains out of reach for the average competitive player.

## The Solution

**Forging** is an AI-powered gameplay analyst that watches your games like a human coach would - understanding the visual gameplay, identifying mistakes, and providing actionable improvement advice.

**It works across game genres.** We're demonstrating two very different games:

| Game | Genre | What Forging Analyzes |
|------|-------|----------------------|
| **Age of Empires II** | RTS | Resource management, build orders, army composition, expansion timing |
| **Counter-Strike 2** | FPS | Crosshair placement, positioning, utility usage, rotation timing, economy decisions |

Same core platform, different game-specific analysis - proving the architecture is extensible.

Upload a gameplay recording, and Forging delivers:
- Game summary with key moments identified
- Specific mistakes with timestamps
- Personalized improvement priorities
- Pattern analysis across your gameplay

## How It Works

1. User selects their game and uploads a replay video (MP4)
2. Gemini 3's multimodal capabilities analyze the video frames with game-specific context
3. Long context window processes the full match (5-40+ minutes depending on game)
4. Structured output returns actionable JSON for the UI
5. User gets a coaching report with timestamped feedback

## Why Gemini 3

This application is only possible with Gemini 3's unique combination:

- **Multimodal video understanding**: Watches gameplay like a human - understands what's happening visually without game API access
- **Long context window**: Processes entire matches without chunking or losing context
- **Structured output**: Returns consistent JSON for seamless UI integration
- **Generalization**: Same model understands RTS resource bars AND FPS crosshair placement

No other model offers this combination for real-time video analysis at this scale.

## Market Opportunity

### The Esports Coaching Boom

The rise of esports has created massive demand for coaching:

| Metric | Value |
|--------|-------|
| Global esports market size (2024) | $2.1B+ |
| Projected market size (2030) | $5B+ |
| Active esports viewers | 500M+ |
| Average coaching rate (amateur) | $30-50/hour |
| Average coaching rate (pro-level) | $100-200/hour |
| Metafy (coaching platform) funding | $50M+ raised |

Tournament prize pools have driven professionalization:
- **The International (Dota 2)**: $40M prize pool
- **Fortnite World Cup**: $30M prize pool
- **CS2 Major Championships**: $1.25M each, multiple per year
- **League of Legends Worlds**: $2.2M prize pool

Where there's money, there's demand for improvement. Forging democratizes access to coaching.

### Target Segments

| Segment | Size | Willingness to Pay |
|---------|------|-------------------|
| Competitive FPS players (CS2, Valorant) | 50M+ monthly | High - coaching is normalized |
| Competitive RTS players (AoE, SC2) | 500K+ monthly | High - already spend on coaching |
| MOBA players (LoL, Dota 2) | 100M+ monthly | High - most professionalized |
| Battle Royale players | 200M+ monthly | Medium - emerging coaching market |

## Competitive Advantage

1. **Game-agnostic architecture** - Same platform works for FPS, RTS, MOBA, etc.
2. **No game integration required** - Works from video alone, no API access needed
3. **First mover in AI coaching** - No comparable multimodal coaching tool exists
4. **Scalable** - Adding a new game requires prompts, not new infrastructure

## Why Two Games for the Demo

Showing both Age of Empires II (RTS) and Counter-Strike 2 (FPS) demonstrates:

1. **Versatility** - Gemini understands completely different visual languages
2. **Extensibility** - Adding games is a configuration change, not a rebuild
3. **Market breadth** - We're not a niche tool for one community

## Business Model (Future)

- **Freemium**: 2 free analyses/month, $10/month for unlimited
- **Pro tier**: $25/month with advanced metrics, trend tracking, meta comparison
- **Game-specific add-ons**: $5/month per additional game
- **API access**: Let content creators and teams integrate analysis

## Roadmap

### Now (Hackathon MVP)
- Video upload and analysis
- Two game support (AoE2, CS2)
- Basic coaching report
- Web interface

### Next
- Additional games (Valorant, League of Legends, Dota 2)
- Multi-game trend tracking per user
- Rank-specific advice calibration

### Vision: Full Player Skill Profile

Inspired by tools like trophi.ai (Rocket League coaching) and Korean esports analytics platforms, we envision Forging evolving into a comprehensive skill development platform:

**Skill Radar Charts**
- Visual breakdown of core competencies per game
- For CS2: Mechanics, Positioning, Utility, Game Sense, Economy
- For AoE2: Macro, Micro, Build Orders, Map Control, Adaptation
- Track how each skill area evolves over time

**Graded Skill Metrics**
- Detailed scoring (C+ to S+ scale) on granular skills
- APM, map awareness, resource efficiency, kill engagement rate
- Compare your metrics against players at your rank and above

**Personalized Learning Paths**
- Rank-specific skill trees ("Gold to Platinum Path")
- Step-by-step skill progression based on your weaknesses
- "Master these 3 fundamentals before moving to advanced techniques"

**Interactive Training Recommendations**
- Link analysis insights to specific practice routines
- "Your crosshair placement is weak → Try aim trainer workshop X"
- "Your build order deviates at 8 min → Practice this timing drill"

This transforms Forging from a post-game analysis tool into a complete coaching platform - not just telling you what went wrong, but guiding you on exactly how to improve.

### Later
- Real-time streaming analysis
- Team/squad analysis for team games
- Integration with streaming platforms (Twitch clips)
- Mobile app for on-the-go review

## Team

Solo developer with:
- Software engineering background
- Active competitive gamer (AoE2, CS2)
- Understanding of both the technical and domain challenges
