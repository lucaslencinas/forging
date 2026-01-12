"""
Age of Empires II: Definitive Edition strategic knowledge for AI coaching.
This knowledge base is used to help the AI understand game context and provide better tips.

Sources:
- https://buildorderguide.com/
- https://aoecompanion.com/build-guides
- https://ageofnotes.com/beginners/hera-strategy-guide-2025/
- https://www.aoebuilds.com/main-build-orders
- https://ageofempires.fandom.com/wiki/Build_order
- https://diamondlobby.com/age-of-empires-2/strategy/
- https://www.redbull.com/us-en/age-of-empires-2-definitive-edition-tips-guide
"""

AOE2_KNOWLEDGE = """
## AOE2 STRATEGIC KNOWLEDGE BASE

### STANDARD DARK AGE OPENING (All Build Orders)
- First 6 villagers → Sheep (under TC)
- Next 4 villagers → Wood (build lumber camp)
- Villager 11 → Lure first Boar to TC
- Villagers 12-13 → Under TC (berries or boar)
- Villager 14 → Lure second Boar (when first boar has ~160 food left)
- Villager 15 → Build Mill at berries
- Villagers 16-17 → Berries

### COMMON BUILD ORDERS & TIMINGS

**22 Pop Archers (Feudal Rush)**
- 22 villagers + Feudal Age click
- Reaches Feudal around 10:00 game time (~6:40 real time)
- Two Archery Ranges producing continuously
- Best for: Britons, Ethiopians, Mayans, Vietnamese

**21 Pop Scouts**
- 21 villagers + Feudal Age click
- Reaches Feudal around 9:30 game time (~6:20 real time)
- Stable producing 3-5 scouts
- Best for: Franks, Huns, Mongols, Lithuanians

**20 Pop Men-at-Arms (M@A Rush)**
- 20 villagers + Feudal Age click (aggressive)
- Barracks at pop 17-18
- 3-4 Militia → upgrade to Men-at-Arms in Feudal
- Hits enemy around 7:30-8:00 game time (~5:00-5:20 real time)
- Best for: Goths, Bulgarians, Japanese, Vikings

**Drush (Dark Age Rush)**
- Barracks at pop 14-15
- 3 Militia sent to enemy base in Dark Age
- Goal: Distract enemy, delay their economy, NOT necessarily kill villagers
- Transitions into: Fast Castle or Archers
- Best for: Aztecs, Japanese, Vikings

**Fast Castle (FC)**
- 27-28 villagers + click Castle Age
- Reaches Castle around 16:00-17:00 game time (~11:00 real time)
- Goal: Reach Castle Age quickly for Knights/Crossbows/Boom
- Risk: Vulnerable to Feudal aggression

**Drush → Fast Castle**
- 3 Militia to distract enemy while walling
- Then transition to Fast Castle
- Safer than pure FC on open maps

### EARLY GAME TECHNIQUES

**Sheep Management**
- Only kill ONE sheep at a time (others decay and lose food)
- Optimal: 6 villagers on sheep
- Move new sheep under TC so they don't get stolen
- Scout should find all 8 sheep quickly

**Boar Luring**
- Villager must shoot boar TWICE to make it chase (1 hit in DE)
- Garrison luring villager in TC when boar arrives
- Other villagers attack boar under TC
- Second boar: lure when first boar has ~160 food left
- TC fire can weaken boar to protect villagers

**Deer Luring/Pushing**
- Scout pushes deer toward TC (deer flee opposite direction)
- Saves 100 wood (no Mill needed) + villager walking time
- Usually push 2 deer maximum
- TRADE-OFF: Scout is busy pushing = not scouting enemy
- On closed maps (Arena): Always push deer
- On open maps (Arabia): Consider skipping if expecting early aggression

**Scouting Priorities**
1. Find your sheep (4 near TC, 4 more nearby)
2. Find your 2 boars
3. Find your berries
4. Find your gold/stone
5. Scout enemy base (see their strategy)
6. Optional: Push deer if time permits

### COMMON MISTAKES (What to look for in coaching)

**Critical Mistakes (Big impact)**
- Idle Town Center (especially in Dark/Feudal Age)
- Getting housed (no population space)
- Losing villagers to boar/wolves
- Not scouting enemy strategy
- Floating resources (1000+ unspent food/wood/gold)
- Stopping villager production for military
- Late age-up times

**Medium Mistakes**
- Idle villagers after building completes
- Too many villagers on one resource
- Not adapting to enemy's strategy
- Poor unit composition (countered easily)
- Not walling on open maps
- Forgetting Loom before risky lures

**Minor Issues (Don't over-emphasize)**
- Brief idle time during micro (1-2 seconds)
- Imperfect build order execution
- Suboptimal rally points
- Small army positioning mistakes

### GAME PHASES & TRANSITIONS

**Dark Age (0-10 min game time)**
- Focus: Economy setup, food collection
- Key actions: Sheep → Boar → Berries → Farms
- Scout finds resources and enemy base

**Feudal Age (10-17 min game time)**
- Focus: First military, apply pressure or defend
- Common strategies: Archers, Scouts, M@A, Towers
- Build: Blacksmith, Market (for Castle Age)

**Castle Age (17-30 min game time)**
- Focus: Power spike, expand or attack
- Common units: Knights, Crossbows, Monks, Siege
- Build: Town Centers for boom, Castle for UU

**Imperial Age (30+ min game time)**
- Focus: Late game armies, Trebs, trade
- Research key upgrades
- Army composition matters most

### CIVILIZATION BONUSES TO KNOW

**Strong Early Game (expect aggression)**
- Goths: Cheaper infantry
- Mongols: Faster scouts
- Aztecs: Faster military production
- Lithuanians: Extra food start

**Strong Archers**
- Britons: Extra range
- Ethiopians: Free archer upgrades
- Mayans: Cheaper archers

**Strong Cavalry**
- Franks: Extra HP
- Huns: No houses needed
- Berbers: Faster moving

**Strong Economy**
- Mayans: Longer lasting resources
- Chinese: Extra starting villagers
- Vikings: Free wheelbarrow/handcart

### UNIT IDENTIFICATION

**Infantry**
- Militia: Basic infantry, visible sword
- Men-at-Arms: Upgraded militia, slightly better armor appearance
- Eagles: Mesoamerican infantry, distinctive feathered headdress

**Cavalry**
- Scout Cavalry: Light, fast, visible in Dark Age
- Knights: Heavy cavalry, appears in Castle Age

**Archers**
- Archer: Basic ranged unit
- Skirmisher: Anti-archer, visible extra padding/shield
- Crossbowman: Castle Age archer upgrade
"""
