export function HowItWorks() {
  return (
    <section className="py-24 px-6 border-y border-white/5">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            From replay to<br/>rank-up in minutes
          </h2>
          <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
            Upload your demo, get AI-powered insights instantly.
          </p>
        </div>

        {/* Step-by-Step Flow */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-md md:max-w-none mx-auto">
          {/* Step 1 */}
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-500 flex items-center justify-center text-black font-bold text-xl shadow-lg shadow-amber-500/20">
              1
            </div>
            <div className="rounded-2xl border border-white/10 bg-zinc-950/50 p-6 pt-10 hover:border-white/20 transition-colors">
              <h3 className="text-xl font-semibold text-white mb-2">Select Your Game</h3>
              <p className="text-zinc-400 text-sm mb-4">
                Choose from AoE II, CS2, or other supported titles. Upload your replay file or screen recording.
              </p>
              <div className="h-32 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center text-xs text-zinc-600">
                [Game Selection UI]
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-500 flex items-center justify-center text-black font-bold text-xl shadow-lg shadow-amber-500/20">
              2
            </div>
            <div className="rounded-2xl border border-white/10 bg-zinc-950/50 p-6 pt-10 hover:border-white/20 transition-colors">
              <h3 className="text-xl font-semibold text-white mb-2">AI Processes Gameplay</h3>
              <p className="text-zinc-400 text-sm mb-4">
                Our engine parses every frame, tracking your economy, positioning, and decision-making.
              </p>
              <div className="h-32 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center">
                <div className="flex items-center gap-2 text-amber-500">
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-xs font-mono">Analyzing...</span>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-amber-500 flex items-center justify-center text-black font-bold text-xl shadow-lg shadow-amber-500/20">
              3
            </div>
            <div className="rounded-2xl border border-white/10 bg-zinc-950/50 p-6 pt-10 hover:border-white/20 transition-colors">
              <h3 className="text-xl font-semibold text-white mb-2">Review Timestamped Feedback</h3>
              <p className="text-zinc-400 text-sm mb-4">
                Click on any tip to see the exact moment in your gameplay. Ask the AI coach questions.
              </p>
              <div className="h-32 rounded-lg bg-zinc-900 border border-white/5 p-3 space-y-2">
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-red-500 mt-1.5 shrink-0" />
                  <div className="text-xs text-zinc-500">3:45 - Utility missed</div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-yellow-500 mt-1.5 shrink-0" />
                  <div className="text-xs text-zinc-500">5:12 - Crosshair placement</div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-zinc-500 mt-1.5 shrink-0" />
                  <div className="text-xs text-zinc-500">7:00 - Positioning error</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
