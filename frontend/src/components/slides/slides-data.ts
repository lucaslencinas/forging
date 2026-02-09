import { APP_PATHS_MANIFEST } from "next/constants";

export type SlideType =
  | "hook-industry"
  | "hook-growth"
  | "hook-problem"
  | "hook-coaching-gap"
  | "prize-pools"
  | "intro"
  | "games"
  | "demo-transition"
  | "market"
  | "competitors"
  | "architecture"
  | "architecture-gemini"
  | "architecture-gemini-flow"
  | "roadmap"
  | "closing";

export type SlideSection =
  | "hook"
  | "intro"
  | "demo"
  | "market"
  | "technical"
  | "closing";

export interface Slide {
  id: number;
  type: SlideType;
  section: SlideSection;
  title: string;
  subtitle?: string;
  content: SlideContent;
  notes?: string;
  script?: string;
}

export type SlideContent =
  | HookIndustryContent
  | HookGrowthContent
  | HookProblemContent
  | HookCoachingGapContent
  | PrizePoolsContent
  | IntroContent
  | GamesContent
  | DemoTransitionContent
  | MarketContent
  | CompetitorsContent
  | ArchitectureContent
  | ArchitectureGeminiContent
  | ArchitectureGeminiFlowContent
  | RoadmapContent
  | ClosingContent;

interface HookIndustryContent {
  type: "hook-industry";
  headline: string;
  stats: { value: string; label: string }[];
  image?: string;
  imagePlaceholder?: string;
}

interface HookGrowthContent {
  type: "hook-growth";
  headline: string;
  subheadline: string;
  chartData: { year: number; value: number; projected?: boolean }[];
  source: string;
}

interface HookProblemContent {
  type: "hook-problem";
  headline: string;
  points: {
    title: string;
    description: string;
    image?: string;
    imagePlaceholder?: string;
  }[];
}

interface HookCoachingGapContent {
  type: "hook-coaching-gap";
  headline: string;
  subheadline: string;
  tiers: { level: string; cost: string; description: string }[];
  imagePlaceholder?: string;
}

interface PrizePoolsContent {
  type: "prize-pools";
  headline: string;
  subheadline: string;
  games: { rank: number; name: string; prize: string }[];
  source: string;
}

interface IntroContent {
  type: "intro";
  tagline: string;
  features: string[];
  highlight: string;
}

interface GamesContent {
  type: "games";
  supported: {
    name: string;
    genre: string;
    image: string;
  }[];
  comingSoon: {
    name: string;
    image: string;
  }[];
}

interface DemoTransitionContent {
  type: "demo-transition";
  message: string;
}

interface MarketContent {
  type: "market";
  headline: string;
  stats: { value: string; label: string }[];
  chartData: { year: number; value: number; projected?: boolean }[];
  source: string;
}

interface CompetitorsContent {
  type: "competitors";
  headline: string;
  competitors: {
    name: string;
    games: string;
    limitation: string;
  }[];
  differentiator: string;
}

interface ArchitectureContent {
  type: "architecture";
  pipeline: { step: string; detail: string }[];
}

interface ArchitectureGeminiContent {
  type: "architecture-gemini";
  pipelineSteps: { step: string; detail: string }[];
  geminiFeatures: { step: string; detail: string }[];
}

interface ArchitectureGeminiFlowContent {
  type: "architecture-gemini-flow";
  variant: 1 | 2 | 3 | 4 | 5 | 6 | 7;
}

interface RoadmapContent {
  type: "roadmap";
  variant: 1 | 2 | 3 | 4 | 5 | 6;
  items: {
    status: "done" | "next" | "future";
    label: string;
    description: string;
  }[];
}

interface ClosingContent {
  type: "closing";
  tagline: string;
  badge: string;
}

export const slides: Slide[] = [
  // === HOOK SECTION (Storytelling) ===
  {
    id: 1,
    type: "hook-industry",
    section: "hook",
    title: "The Esports Revolution",
    content: {
      type: "hook-industry",
      headline: "Gaming Has Gone Competitive",
      stats: [
        { value: "640M", label: "esports viewers" },
        { value: "$2.4B", label: "industry in 2025" },
        { value: "500+", label: "pro tournaments/year" },
      ],
      image: "/images/crowd-live-event.png",
    },
    notes: "Open with the scale - this isn't just a hobby anymore",
    script:
      "Esports has gone mainstream. With more than 600 million viewers and a multi-billion dollar industry, competitive play is no longer a niche - it's global entertainment.",
  },
  {
    id: 2,
    type: "hook-growth",
    section: "hook",
    title: "Explosive Growth",
    content: {
      type: "hook-growth",
      headline: "Rapid Market Expansion",
      subheadline: "Esports Market Size (Billions USD)",
      chartData: [
        { year: 2020, value: 0.95 },
        { year: 2022, value: 1.38 },
        { year: 2025, value: 2.4 },
        { year: 2027, value: 3.5, projected: true },
        { year: 2030, value: 5.5, projected: true },
      ],
      source:
        "Statista, Market.us, Polytechnique Insights, Esports Insider 2025",
    },
    notes: "Show the trajectory - this is where the opportunity is",
    script:
      "The esports market has been growing at a rate of 15-20% annually. It is projected to reach $5.5 billions by 2030.",
  },
  {
    id: 3,
    type: "prize-pools",
    section: "hook",
    title: "Top Esports Games 2025",
    content: {
      type: "prize-pools",
      headline: "Where the Money Flows",
      subheadline: "Top Games by Prize Pool (2025)",
      games: [
        { rank: 1, name: "Counter-Strike", prize: "$28.5M" },
        { rank: 2, name: "Dota 2", prize: "$20.2M" },
        { rank: 3, name: "Honor of Kings", prize: "$20.2M" },
        { rank: 4, name: "League of Legends", prize: "$14.4M" },
        { rank: 5, name: "Fortnite", prize: "$10.7M" },
        { rank: 6, name: "Valorant", prize: "$9.6M" },
        { rank: 7, name: "PUBG Mobile", prize: "$8.2M" },
        { rank: 8, name: "Rainbow Six", prize: "$7.1M" },
        { rank: 9, name: "Rocket League", prize: "$6.5M" },
        { rank: 10, name: "Mobile Legends", prize: "$5.8M" },
      ],
      source: "Esports Insider 2025 Year in Review",
    },
    notes:
      "Show competitive money - validates the games we support and coming soon",
    script:
      "Counter-Strike leads with $28.5 million in prize pools. These are the games where players are most hungry to improve - and most willing to invest in coaching.",
  },
  {
    id: 4,
    type: "hook-problem",
    section: "hook",
    title: "The Improvement Challenge",
    content: {
      type: "hook-problem",
      headline: "Everyone Wants to Improve",
      points: [
        {
          title: "Players watch replays",
          description: "Most games let you rewatch your matches",
          image: "/images/CS2-Replay-Controls.png",
        },
        {
          title: "Players study streamers",
          description: "Watching pros play to learn strategies",
          image: "/images/twitch-results-streamers.jpg",
        },
        {
          title: "But spotting your own mistakes?",
          description: "That takes expertise most players don't have",
          image: "/images/frustrated-gamer.jpg",
        },
      ],
    },
    notes: "Build the problem - players try but lack the expertise",
    script:
      "Players at every level try to improve. They watch replays, study streamers, analyze their stats. But spotting your own mistakes - understanding WHY you lost, not just THAT you lost - that takes coaching expertise.",
  },
  {
    id: 5,
    type: "hook-coaching-gap",
    section: "hook",
    title: "The Coaching Gap",
    content: {
      type: "hook-coaching-gap",
      headline: "Expert Coaching is Expensive",
      subheadline: "The path from amateur to pro has a paywall",
      tiers: [
        {
          level: "Casual → Ranked",
          cost: "Free",
          description: "YouTube guides, community tips",
        },
        {
          level: "Ranked → Competitive",
          cost: "$15-40/hr",
          description: "Online coaching sessions",
        },
        {
          level: "Competitive → Pro",
          cost: "$50-100+/hr",
          description: "Elite coaches, team analysts",
        },
      ],
      imagePlaceholder:
        "Split image: left side casual player, right side pro player at tournament",
    },
    notes: "The pain point - coaching exists but isn't accessible",
    script:
      "The problem is access. Many players can go so far with free resources online but improving beyond that? That requires a coach - and that costs quite some money.",
  },
  // === INTRO SECTION ===
  {
    id: 6,
    type: "intro",
    section: "intro",
    title: "Introducing FORGING",
    content: {
      type: "intro",
      tagline: "AI-Powered Coaching for Every Player",
      features: [
        "Upload your gameplay",
        "Get timestamped coaching tips",
        "Chat with full match context",
      ],
      highlight: "Analysis in minutes, not hours",
    },
    notes: "The solution reveal - keep it punchy",
    script:
      "That's why we built FORGING. Upload your gameplay, get AI-powered coaching tips at the exact moments you need to improve and chat with your AI coach who has full context of your entire match.",
  },
  // === GAMES SECTION ===
  {
    id: 7,
    type: "games",
    section: "demo",
    title: "Supported Games",
    content: {
      type: "games",
      supported: [
        {
          name: "Counter-Strike 2",
          genre: "FPS",
          image: "/game-placeholders/cs2.png",
        },
        {
          name: "Age of Empires II",
          genre: "RTS",
          image: "/game-placeholders/aoe2.png",
        },
      ],
      comingSoon: [
        { name: "Valorant", image: "/images/games/valorant-square.png" },
        { name: "League of Legends", image: "/images/games/lol-square.png" },
        { name: "Dota 2", image: "/images/games/dota2-square.png" },
        {
          name: "Rocket League",
          image: "/images/games/rocketleague-square.jpg",
        },
      ],
    },
    notes: "Show game diversity - FPS and RTS prove versatility",
    script:
      "We currently support Counter-Strike and Age of Empires proving the architecture works across completely different game genres.",
  },
  // === DEMO TRANSITION ===
  {
    id: 8,
    type: "demo-transition",
    section: "demo",
    title: "Live Demo",
    content: {
      type: "demo-transition",
      message: "Let me show you how it works",
    },
    notes: "Transition slide - switch to browser for live demo",
    script:
      "Let me show you how it works with a live demo. [SWITCH TO BROWSER]",
  },
  // === MARKET SECTION ===
  {
    id: 9,
    type: "market",
    section: "market",
    title: "Market Opportunity",
    content: {
      type: "market",
      headline: "A Growing Opportunity",
      stats: [
        { value: "$2.4B", label: "market 2025" },
        { value: "$5.5B+", label: "projected 2030" },
        { value: "15-20%", label: "annual growth" },
      ],
      chartData: [
        { year: 2020, value: 0.95 },
        { year: 2022, value: 1.38 },
        { year: 2025, value: 2.4 },
        { year: 2027, value: 3.5, projected: true },
        { year: 2030, value: 5.5, projected: true },
      ],
      source:
        "Statista, Market.us, Polytechnique Insights, Esports Insider 2025",
    },
    notes: "Market size justifies the solution",
    script:
      "Market size justifies the solution. Coaching and improvement tools are a growing segment of this ecosystem.",
  },
  // === COMPETITORS SECTION ===
  {
    id: 10,
    type: "competitors",
    section: "market",
    title: "Competitive Landscape",
    content: {
      type: "competitors",
      headline: "The AI Coaching Space",
      competitors: [
        {
          name: "Trophi.ai",
          games: "Rocket League + Racing Sims",
          limitation: "PC only, narrow genre focus",
        },
        {
          name: "Omnic.ai",
          games: "Valorant, Fortnite, RL, OW2",
          limitation: "FPS/Sports only, no RTS support",
        },
        {
          name: "iTero (GIANTX)",
          games: "League of Legends only",
          limitation: "Single game, acquired for multi-millions",
        },
      ],
      differentiator:
        "FORGING is built to be game-agnostic. With minimal effort, we can analyze any game genre - FPS, RTS, MOBA, and beyond.",
    },
    notes: "Show we know the space and have a unique angle",
    script:
      "There are competitors in this space but most of them focus on a single game or a single genre. FORGING is game-agnostic. The same platform works across genres.",
  },
  // === ARCHITECTURE SECTION ===
  {
    id: 11,
    type: "architecture",
    section: "technical",
    title: "How It Works",
    content: {
      type: "architecture",
      pipeline: [
        { step: "Upload", detail: "Replay file or video" },
        { step: "Parse", detail: "Game-specific extractors" },
        { step: "Analyze", detail: "Gemini multimodal AI" },
        { step: "Generate", detail: "Timestamped coaching" },
      ],
    },
    notes: "Technical credibility - simple pipeline view",
    script:
      "The pipeline is simple: you upload your replay or video, we parse it with game-specific extractors, analyze it with Gemini's multimodal AI, and generate timestamped coaching tips.",
  },
  {
    id: 12,
    type: "architecture-gemini",
    section: "technical",
    title: "Powered by Gemini",
    content: {
      type: "architecture-gemini",
      pipelineSteps: [
        { step: "Upload", detail: "Replay file or video" },
        { step: "Parse", detail: "Game-specific extractors" },
        { step: "Analyze", detail: "Gemini multimodal AI" },
        { step: "Generate", detail: "Timestamped coaching" },
      ],
      geminiFeatures: [
        { step: "File API", detail: "700MB videos, 30min matches" },
        { step: "Multimodal", detail: "Video + replay data + chat" },
        { step: "Thinking", detail: "Configurable reasoning depth" },
        { step: "Interactions API", detail: "Multi-agent context chaining" },
        { step: "TTS", detail: "Voice coaching" },
        { step: "Structured Output", detail: "Native JSON schema responses" },
      ],
    },
    notes: "Emphasize Gemini capabilities - 6 features",
    script:
      "What makes this possible is Gemini. We built this platform using the File API, Multimodal capabilities, multiple Thinking levels, the Interactions API, the Text to Speech models and Structured Outputs where needed.",
  },
  // === ROADMAP SECTION ===
  {
    id: 13,
    type: "roadmap",
    section: "technical",
    title: "Roadmap",
    subtitle: "",
    content: {
      type: "roadmap",
      variant: 4,
      items: [
        {
          status: "done",
          label: "Current",
          description: "Video Analysis\nVoice Coaching\nChat with Coach",
        },
        {
          status: "next",
          label: "Progression",
          description: "Track skill over time",
        },
        {
          status: "future",
          label: "Team Voice",
          description:
            '"You saw an enemy at 3:20 but\ndidn\'t call out where he was heading"',
        },
        {
          status: "future",
          label: "Input Analysis",
          description:
            '"You created 12 galleys by clicking\nthe dock—set up a hotkey"',
        },
        {
          status: "future",
          label: "More Games",
          description: "Valorant, LoL, Dota 2",
        },
      ],
    },
    notes: "Horizontal timeline showing what's done and what's next",
    script:
      "Currently we have Video analysis, voice coaching, and chat. Soon, we will build a skill progression tracking. And later on we will include team voice and keyboard/mouse analysis.",
  },
  // === CLOSING SECTION ===
  {
    id: 14,
    type: "closing",
    section: "closing",
    title: "Built for Gemini",
    content: {
      type: "closing",
      tagline: "The Future of Accessible Esports Coaching",
      badge: "Built for Gemini API Developer Competition",
    },
    notes: "Strong close - tie back to hackathon",
    script: "FORGING is the future of accessible esports coaching. Thank you.",
  },
];
