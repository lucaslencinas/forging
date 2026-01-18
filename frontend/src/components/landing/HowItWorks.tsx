const steps = [
  {
    number: "1",
    title: "Upload your gameplay",
    description:
      "Record your game and upload the video. We support MP4 files up to 700MB, 30 minutes max.",
    icon: "📤",
  },
  {
    number: "2",
    title: "AI analyzes every moment",
    description:
      "Our AI watches your gameplay and identifies key moments, mistakes, and opportunities.",
    icon: "🤖",
  },
  {
    number: "3",
    title: "Get timestamped tips",
    description:
      "Receive coaching tips linked to specific moments in your video. Click to jump right to that moment.",
    icon: "💡",
  },
];

export function HowItWorks() {
  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          How It Works
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          Get personalized coaching in three simple steps
        </p>

        <div className="mt-12 grid gap-8 sm:grid-cols-3">
          {steps.map((step) => (
            <div key={step.number} className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-orange-500/20 to-amber-500/20 text-3xl">
                {step.icon}
              </div>
              <div className="mt-4 text-sm font-medium text-orange-500">
                Step {step.number}
              </div>
              <h3 className="mt-2 text-lg font-semibold text-white">
                {step.title}
              </h3>
              <p className="mt-2 text-sm text-zinc-400">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
