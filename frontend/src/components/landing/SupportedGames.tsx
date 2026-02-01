"use client";

import { HorizontalCarousel } from "../HorizontalCarousel";

const games = [
  {
    name: "Age of Empires II",
    subtitle: "Definitive Edition",
    icon: "🏰",
    status: "available" as const,
    fileType: ".aoe2record",
  },
  {
    name: "Counter-Strike 2",
    subtitle: "Demo Analysis",
    icon: "🎯",
    status: "available" as const,
    fileType: ".dem",
  },
  {
    name: "Rocket League",
    subtitle: "Coming Soon",
    icon: "🚀",
    status: "coming-soon" as const,
  },
  {
    name: "Dota 2",
    subtitle: "Coming Soon",
    icon: "🗡️",
    status: "coming-soon" as const,
  },
  {
    name: "League of Legends",
    subtitle: "Coming Soon",
    icon: "⚔️",
    status: "coming-soon" as const,
  },
];

export function SupportedGames() {
  return (
    <section className="px-6 py-16 bg-gradient-to-b from-zinc-900 via-zinc-900 to-purple-950/10">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          Supported Games
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Upload your gameplay and get AI-powered coaching
        </p>

        <div className="mt-12">
          <HorizontalCarousel>
            {games.map((game) => (
              <div
                key={game.name}
                className={`relative flex-shrink-0 w-64 rounded-xl border p-6 transition-all ${
                  game.status === "available"
                    ? "border-zinc-700/50 bg-gradient-to-br from-zinc-800/80 to-zinc-800/40 hover:border-zinc-600 hover:shadow-lg hover:shadow-purple-500/5"
                    : "border-zinc-800/50 bg-zinc-900/50 opacity-60"
                }`}
              >
                <span className="text-4xl">{game.icon}</span>
                <h3 className="mt-4 text-lg font-semibold text-white">
                  {game.name}
                </h3>
                <p className="text-sm text-zinc-400">{game.subtitle}</p>
                {game.fileType && (
                  <p className="mt-2 text-xs text-zinc-500">
                    File type: {game.fileType}
                  </p>
                )}
                {game.status === "coming-soon" && (
                  <span className="absolute right-4 top-4 rounded-full bg-zinc-700 px-2 py-1 text-xs text-zinc-300">
                    Soon
                  </span>
                )}
              </div>
            ))}
          </HorizontalCarousel>
        </div>
      </div>
    </section>
  );
}
