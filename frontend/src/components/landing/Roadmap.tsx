const columns = [
  {
    title: "Now",
    subtitle: "Available today",
    color: "green",
    items: [
      { title: "Video Analysis", description: "AI watches your gameplay frame-by-frame, no game API required" },
      { title: "Cross-Genre Support", description: "Same platform for RTS (AoE2) and FPS (CS2) games" },
      { title: "AI Chat Follow-ups", description: "Ask questions about specific moments in your match" },
    ],
  },
  {
    title: "Next",
    subtitle: "Coming soon",
    color: "orange",
    items: [
      { title: "Skill Radar Charts", description: "Visual breakdown of Mechanics, Positioning, Game Sense" },
      { title: "Graded Metrics", description: "C+ to S+ scoring on APM, map awareness, resource efficiency" },
      { title: "More Games", description: "Valorant, League of Legends, Dota 2" },
    ],
  },
  {
    title: "Later",
    subtitle: "On our radar",
    color: "zinc",
    items: [
      { title: "Personalized Learning Paths", description: "Rank-specific skill trees like \"Gold to Platinum Path\"" },
      { title: "Training Recommendations", description: "Link weaknesses to practice drills and workshop maps" },
      { title: "Team Analysis", description: "Squad-level feedback for team coordination" },
    ],
  },
];

const colorStyles = {
  green: {
    header: "text-green-500",
    border: "border-green-500/30",
    bg: "bg-green-500/5",
    dot: "bg-green-500",
  },
  orange: {
    header: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/5",
    dot: "bg-amber-500",
  },
  zinc: {
    header: "text-zinc-400",
    border: "border-zinc-600/30",
    bg: "bg-zinc-500/5",
    dot: "bg-zinc-500",
  },
};

export function Roadmap() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          Product Roadmap
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Our vision for the future of AI coaching
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-3 max-w-md sm:max-w-none mx-auto">
          {columns.map((column) => {
            const styles = colorStyles[column.color as keyof typeof colorStyles];
            return (
              <div
                key={column.title}
                className={`rounded-xl border ${styles.border} ${styles.bg} p-6`}
              >
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${styles.dot}`} />
                  <h3 className={`text-lg font-semibold ${styles.header}`}>
                    {column.title}
                  </h3>
                </div>
                <p className="mt-1 text-xs text-zinc-500">{column.subtitle}</p>

                <div className="mt-6 space-y-4">
                  {column.items.map((item) => (
                    <div
                      key={item.title}
                      className="rounded-lg bg-zinc-800/50 p-4"
                    >
                      <h4 className="font-medium text-white">{item.title}</h4>
                      <p className="mt-1 text-sm text-zinc-400">
                        {item.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
