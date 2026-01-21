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
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          Supported Games
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Upload your gameplay and get AI-powered coaching
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {games.map((game) => (
            <div
              key={game.name}
              className={`relative rounded-xl border p-6 transition-all ${
                game.status === "available"
                  ? "border-zinc-700 bg-zinc-800/50 hover:border-zinc-600"
                  : "border-zinc-800 bg-zinc-900/50 opacity-60"
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
        </div>
      </div>
    </section>
  );
}
