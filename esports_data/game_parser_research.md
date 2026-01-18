# Game Parser Research for Analysis Tools

*Compiled: January 2025*

---

## Executive Summary

Research into replay parsing capabilities for top esports games, evaluating suitability for building analysis tools similar to Age of Empires II.

### Priority Ranking (User Preference)

| Priority | Game | Reasoning |
|----------|------|-----------|
| 1 | **Rocket League** | Easy implementation + new game genre |
| 2 | **Dota 2** | Easy implementation + large market share |
| 3 | **League of Legends** | Massive opportunity (largest audience) |
| 4 | **StarCraft II** | Easy implementation (same RTS genre) |

---

## Games Already Implemented

- **Age of Empires II** - `.aoe2record` files with mgz parser
- **Counter-Strike 2** - `.dem` files with awpy parser

---

## Detailed Parser Analysis

### 1. Rocket League (Priority #1)

**Market Data:**
- Prize Pool 2025: $8.2M
- Peak Viewers: 397K
- Unique selling point: Physics-based gameplay, different from existing games

#### Recommended Parsers

| Parser | Language | Status | Features |
|--------|----------|--------|----------|
| [rlrml/subtr-actor](https://github.com/rlrml/subtr-actor) | Rust + **Python bindings** | ✅ Active (Nov 2024) | **BEST** - Frame-by-frame, NumPy arrays output |
| [nickbabcock/boxcars](https://github.com/nickbabcock/boxcars) | Rust | ✅ Active (Dec 2025) | Core parser, very fast |
| [nickbabcock/rrrocket](https://github.com/nickbabcock/rrrocket) | Rust CLI | ✅ Active (Dec 2025) | JSON output, 20k replays/sec for headers |
| [nickbabcock/rl-web](https://github.com/nickbabcock/rl-web) | Web | ✅ Active | Browser-based parsing |
| [jjbott/RocketLeagueReplayParser](https://github.com/jjbott/RocketLeagueReplayParser) | C# | ✅ Active | Original reference implementation |

#### Deprecated (AVOID)
- ~~[SaltieRL/carball](https://github.com/SaltieRL/carball)~~ - **PROJECT SHUTDOWN**

#### Data Available
- Frame-by-frame car positions, rotations, physics
- Ball trajectory and physics
- Boost usage, demolitions
- Goals, saves, assists
- All tick data (~120 ticks/second)

#### Resources
- [ballchasing.com](https://ballchasing.com/) - 145M+ replays available
- File format: `.replay`

---

### 2. Dota 2 (Priority #2)

**Market Data:**
- Prize Pool 2025: $22.5M (#2 overall)
- Peak Viewers: 1.79M
- Established MOBA with massive competitive scene

#### Recommended Parsers

| Parser | Language | Status | Features |
|--------|----------|--------|----------|
| [skadistats/clarity](https://github.com/skadistats/clarity) | Java | ✅ Active (Feb 2025) | **BEST** - "Comically fast", full entities, also supports CS2 & Deadlock |
| [dotabuff/manta](https://github.com/dotabuff/manta) | Go | ✅ Active (Dec 2025) | Production-grade (powers Dotabuff.com) |
| [Rupas1k/source2-demo](https://github.com/Rupas1k/source2-demo) | Rust | ✅ Active (Jan 2026) | Newest, multi-game (Dota 2, CS2, Deadlock) |
| [odota/rapier](https://github.com/odota/rapier) | JavaScript | ✅ Active | Powers OpenDota |

#### Deprecated (AVOID)
- ~~[skadistats/smoke](https://github.com/skadistats/smoke)~~ - Old, unmaintained
- ~~OpenDota API~~ - Only match results, no tick-by-tick data

#### Data Available
- Tick-by-tick hero positions
- Spell casts, item purchases
- Combat log (damage, kills, healing)
- Creep spawns, Roshan kills
- Ward placements, vision

#### Resources
- [OpenDota](https://www.opendota.com/) - Match data API (not tick data)
- [Dotabuff](https://www.dotabuff.com/) - Statistics
- File format: `.dem`

---

### 3. League of Legends (Priority #3)

**Market Data:**
- Prize Pool 2025: $14.7M
- Peak Viewers: **6.75M** (#1 - largest audience by far)
- 180M+ monthly players - biggest player base

#### The Challenge

**No working replay parser exists.**
- `.rofl` format broke in patch 14.9 (2024)
- [roflxd](https://github.com/fraxiinus/roflxd) - "Only works on pre-14.9 files"

#### Alternative Approaches

| Approach | Tool | Notes |
|----------|------|-------|
| **Riot API** | [developer.riotgames.com](https://developer.riotgames.com/) | Match stats, timelines, but not frame-by-frame positions |
| **Video Analysis** | [pyLoL](https://github.com/league-of-legends-replay-extractor/pyLoL) | Computer vision on VODs |
| **Riot API Timeline** | Match-V5 API | Events with timestamps (kills, objectives) but not positions |

#### Riot Games API

**Endpoint:** https://developer.riotgames.com/

| API | Data Available |
|-----|----------------|
| Match-V5 | Match metadata, participants, stats |
| Match Timeline | Events with timestamps (kills, dragons, towers) |
| Spectator-V5 | Live game data (limited) |
| Champion Mastery | Player progression |

**Limitations:**
- No frame-by-frame position data
- No replay file parsing
- Rate limited

#### Why Still Consider LoL

| Pro | Details |
|-----|---------|
| **#1 Viewership** | 6.75M peak - unmatched |
| **Largest player base** | 180M+ monthly |
| **Riot API** | Well-documented, reliable |
| **Cultural reach** | Arcane, K/DA, mainstream recognition |
| **Same company as Valorant** | Future potential |

#### Resources
- [Riot Developer Portal](https://developer.riotgames.com/)
- [Riot API Documentation](https://developer.riotgames.com/docs/lol)
- File format: `.rofl` (broken parsers)

---

### 4. StarCraft II (Priority #4)

**Market Data:**
- Prize Pool 2025: ~$2M
- Same RTS genre as Age of Empires II
- Official Blizzard support

#### Recommended Parsers

| Parser | Language | Status | Features |
|--------|----------|--------|----------|
| [sc2reader](https://github.com/GraylinKim/sc2reader) | **Python** | ✅ Active | **BEST** - Full gamestate, positions, events |
| [zephyrus-sc2-parser](https://github.com/ZephyrBlu/zephyrus-sc2-parser) | **Python** | ✅ Active | Gamestate at 5-second intervals, powers zephyrus.gg |
| [Blizzard/s2protocol](https://github.com/Blizzard/s2protocol) | **Python** | ✅ Official | Official Blizzard tool, all protocol versions |

#### Data Available
- Unit positions over time
- Build orders, resource collection
- Army compositions
- APM, EPM metrics
- All player commands

#### Resources
- Official replay packs from Blizzard
- [spawningtool.com](https://spawningtool.com/) - Build orders
- File format: `.SC2Replay`

---

## Games to Avoid

| Game | Score | Reason |
|------|-------|--------|
| **Apex Legends** | 2/10 | No replay system exists |
| **Overwatch 2** | 3/10 | Proprietary, ephemeral replays, no parser |
| **Valorant** | 4/10 | New replay system can't export files, no parser |
| **Fighting Games** | 3/10 | In-game only, no file export |

---

## Comparison Matrix

| Game | Parser Available | Python? | Tick Data | Market Size | Difficulty |
|------|------------------|---------|-----------|-------------|------------|
| **Rocket League** | subtr-actor | ✅ Bindings | ✅ NumPy | $8.2M | Easy |
| **Dota 2** | clarity/manta | ❌ Java/Go | ✅ Full | $22.5M | Medium |
| **League of Legends** | None (API only) | ✅ API | ❌ No | $14.7M / 6.75M viewers | Hard |
| **StarCraft II** | sc2reader | ✅ Native | ✅ Full | $2M | Easy |

---

## AI Coaching Competitors

### Existing AI Coaching Platforms

| Platform | URL | Games Supported | Approach |
|----------|-----|-----------------|----------|
| **Trophi.ai** | [trophi.ai](https://www.trophi.ai/) | Multiple | AI coaching platform |
| **Statup.gg** | [statup.gg](https://statup.gg/) | Valorant, CS2 | Performance analytics |
| **Omnic.ai** | [omnic.ai](https://www.omnic.ai/) | Overwatch 2, Fortnite, Valorant | AI-powered VOD review |
| **Razer Game Co-AI** | [razer.ai/game-co-ai](https://www.razer.ai/game-co-ai/) | Multiple | Razer's AI gaming assistant |

### Competitive Landscape Notes

- Most focus on FPS games (Valorant, CS2, Overwatch)
- Video/VOD analysis is common approach
- Integration with streaming platforms
- Personalized improvement recommendations

---

## Recommended Implementation Roadmap

### Phase 1: Easy Wins
1. **Rocket League** - subtr-actor gives Python bindings + NumPy
2. **StarCraft II** - sc2reader is pure Python, same RTS genre

### Phase 2: High Value
3. **Dota 2** - Build wrapper around clarity (Java) or manta (Go)

### Phase 3: Massive Opportunity
4. **League of Legends** - Two options:
   - Riot API for match statistics + timeline events
   - Computer vision for video analysis (harder but more data)

---

## Key Parser Links

### Rocket League
- https://github.com/rlrml/subtr-actor (Python bindings)
- https://github.com/nickbabcock/boxcars (Core Rust parser)
- https://github.com/nickbabcock/rrrocket (CLI tool)
- https://github.com/nickbabcock/rl-web (Web interface)
- https://github.com/jjbott/RocketLeagueReplayParser (C#)

### Dota 2
- https://github.com/skadistats/clarity (Java - best features)
- https://github.com/dotabuff/manta (Go - production grade)
- https://github.com/Rupas1k/source2-demo (Rust - newest)

### StarCraft II
- https://github.com/GraylinKim/sc2reader (Python)
- https://github.com/ZephyrBlu/zephyrus-sc2-parser (Python)
- https://github.com/Blizzard/s2protocol (Official Python)

### League of Legends
- https://developer.riotgames.com/ (Official API)
- https://github.com/league-of-legends-replay-extractor/pyLoL (Video analysis)

---

*Last updated: January 2025*
