const features = [
  {
    title: "Economy & Resource Coaching",
    description:
      "Get advice on buy decisions, resource management, and economic strategy for CS2 and RTS games.",
    icon: "💰",
  },
  {
    title: "Personalized Training Drills",
    description:
      "Based on your weaknesses, get recommended aim trainers, workshop maps, and practice routines.",
    icon: "🎯",
  },
  {
    title: "Hand & Keyboard Camera",
    description:
      "Upload a second video of your hands to analyze mechanics, key bindings, and APM.",
    icon: "⌨️",
  },
];

export function Features() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          What We&apos;re Building
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Features coming to make your coaching even better
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="relative rounded-xl border border-orange-500/20 bg-gradient-to-br from-orange-500/5 to-amber-500/5 p-6"
            >
              <span className="absolute right-4 top-4 rounded-full bg-orange-500/20 px-2 py-1 text-xs text-orange-400">
                Building
              </span>
              <span className="text-3xl">{feature.icon}</span>
              <h3 className="mt-4 text-lg font-semibold text-white">
                {feature.title}
              </h3>
              <p className="mt-2 text-sm text-zinc-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
