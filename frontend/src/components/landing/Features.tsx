export function Features() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            Why Forging?
          </h2>
          <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
            Pro-level coaching without the pro-level price tag
          </p>
        </div>

        {/* Problem/Solution Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16 max-w-md md:max-w-none mx-auto">
          {/* The Problem */}
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
            <h3 className="text-lg font-semibold text-red-400 mb-4 flex items-center gap-2">
              <span className="text-xl">✗</span> The Old Way
            </h3>
            <ul className="space-y-3 text-zinc-400 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>Human coaches cost <strong className="text-white">$50-150/hour</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>Wait days or weeks for session availability</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>Coaches specialize in one game only</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>
                <span>Manual VOD review is slow and incomplete</span>
              </li>
            </ul>
          </div>

          {/* The Solution */}
          <div className="rounded-2xl border border-green-500/20 bg-green-500/5 p-6">
            <h3 className="text-lg font-semibold text-green-400 mb-4 flex items-center gap-2">
              <span className="text-xl">✓</span> The Forging Way
            </h3>
            <ul className="space-y-3 text-zinc-400 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span>
                <span>Instant analysis for <strong className="text-white">free during beta</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span>
                <span>Results in under 3 minutes, available 24/7</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span>
                <span>Same platform works across game genres</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-400 mt-0.5">•</span>
                <span>AI watches every frame - nothing missed</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-md md:max-w-none mx-auto">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/[0.07] transition-all">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Sees What a Coach Sees</h3>
            <p className="text-zinc-400 text-sm">
              Gemini AI watches your gameplay frame-by-frame, reading resources, positioning, and decision-making - no game API required.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/[0.07] transition-all">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Ask Follow-up Questions</h3>
            <p className="text-zinc-400 text-sm">
              &quot;Why did I lose that fight?&quot; Chat with the AI about specific moments. It remembers the full match context.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/[0.07] transition-all">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center mb-4">
              <svg className="w-6 h-6 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Works Across Genres</h3>
            <p className="text-zinc-400 text-sm">
              Same AI analyzes RTS economy, FPS aim, and tactical positioning. Adding new games is configuration, not a rebuild.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
