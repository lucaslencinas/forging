const columns = [
  {
    title: "Now",
    subtitle: "Available today",
    color: "green",
    items: [
      { title: "Video Analysis", description: "AI-powered gameplay review" },
      { title: "Voice Coaching", description: "Audio tips synced to video" },
    ],
  },
  {
    title: "Next",
    subtitle: "Coming soon",
    color: "orange",
    items: [
      { title: "Progress Dashboard", description: "Track improvement over time" },
      { title: "Shareable Highlights", description: "Auto-generate clips for social" },
    ],
  },
  {
    title: "Later",
    subtitle: "On our radar",
    color: "zinc",
    items: [
      { title: "Team Voice Comms", description: "Analyze team communication" },
      { title: "Coaching Marketplace", description: "Connect with human coaches" },
    ],
  },
];

const colorStyles = {
  green: {
    header: "text-green-400",
    border: "border-green-500/30",
    bg: "bg-green-500/5",
    dot: "bg-green-500",
  },
  orange: {
    header: "text-orange-400",
    border: "border-orange-500/30",
    bg: "bg-orange-500/5",
    dot: "bg-orange-500",
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
    <section className="px-6 py-16 bg-gradient-to-b from-zinc-900 via-zinc-900 to-purple-950/10">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          Product Roadmap
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Our vision for the future of AI coaching
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-3">
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
