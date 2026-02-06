export function SupportedGames() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            Supported Games
          </h2>
          <p className="text-zinc-500 text-lg">
            Precision analysis for competitive gaming
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-md md:max-w-4xl mx-auto">
          {/* CS2 - Primary Featured Game */}
          <div className="relative group overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 hover:border-white/20 transition-all duration-500">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-white text-sm">
                1
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Counter-Strike 2</h3>
                <span className="text-[10px] font-medium text-amber-400 uppercase tracking-wider">Primary Focus</span>
              </div>
            </div>

            <p className="text-zinc-400 text-sm mb-4">
              Crosshair placement, utility usage, positioning errors, and economy decisions.
            </p>

            {/* Mock Analysis Preview - CS2 Style */}
            <div className="rounded-xl bg-black/60 border border-white/10 overflow-hidden">
              {/* Video Area with actual screenshot */}
              <div className="aspect-video relative">
                <img
                  src="/game-placeholders/cs2-dust2.png"
                  alt="CS2 de_dust2 gameplay"
                  className="w-full h-full object-cover"
                />
                {/* Dark overlay for readability */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />

                {/* Floating Tip Overlay */}
                <div className="absolute top-3 right-3 max-w-[200px] bg-zinc-900/95 border border-white/10 rounded-lg p-2.5 backdrop-blur-sm shadow-xl">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-mono text-amber-400 bg-amber-500/20 px-1.5 py-0.5 rounded">0:30</span>
                    <span className="text-[8px] uppercase tracking-wider text-zinc-500">AIM</span>
                  </div>
                  <p className="text-[11px] text-zinc-300 leading-tight">
                    Crosshair too low - aim at head height before peeking corners.
                  </p>
                </div>

                {/* Map label */}
                <div className="absolute bottom-3 left-3 text-xs text-white/70 font-medium bg-black/50 px-2 py-1 rounded backdrop-blur-sm">
                  de_dust2
                </div>
              </div>

              {/* Mock Tips Sidebar Preview */}
              <div className="p-3 border-t border-white/5 space-y-2">
                <div className="flex items-start gap-2 p-2 rounded bg-amber-500/10 border border-amber-500/30">
                  <span className="text-[10px] font-mono text-black bg-amber-500 px-1.5 py-0.5 rounded">0:30</span>
                  <span className="text-[11px] text-zinc-300">Crosshair placement needs work</span>
                </div>
                <div className="flex items-start gap-2 p-2 rounded bg-white/5 border border-white/5">
                  <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">1:45</span>
                  <span className="text-[11px] text-zinc-500">Economy: Buy armor first</span>
                </div>
                <div className="flex items-start gap-2 p-2 rounded bg-white/5 border border-white/5">
                  <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">2:30</span>
                  <span className="text-[11px] text-zinc-500">Check corners before entering site</span>
                </div>
                <div className="flex items-start gap-2 p-2 rounded bg-white/5 border border-white/5">
                  <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded">3:15</span>
                  <span className="text-[11px] text-zinc-500">Use utility to clear common spots</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - AoE2 + Coming Soon */}
          <div className="space-y-6">
            {/* AoE2 - Secondary Game */}
            <div className="relative group overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 hover:border-white/20 transition-all duration-500">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-white text-sm">
                  2
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">Age of Empires II</h3>
                  <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">Also Supported</span>
                </div>
              </div>

              <p className="text-zinc-400 text-sm mb-4">
                Build order analysis, economy tracking, military composition, and age-up timings.
              </p>

              {/* Preview with actual screenshot */}
              <div className="rounded-xl overflow-hidden border border-white/10 relative">
                <img
                  src="/game-placeholders/aoe2-gameplay.png"
                  alt="Age of Empires II gameplay"
                  className="w-full h-32 object-cover object-top"
                />
                {/* Dark overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

                {/* Age indicators overlay */}
                <div className="absolute bottom-2 left-2 right-2 flex items-center justify-center gap-3 text-xs">
                  <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-2 py-1 rounded">
                    <div className="w-5 h-5 rounded bg-green-500/30 flex items-center justify-center text-[9px] text-green-400 font-medium">II</div>
                    <span className="text-zinc-400 text-[10px]">Feudal</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-2 py-1 rounded">
                    <div className="w-5 h-5 rounded bg-blue-500/30 flex items-center justify-center text-[9px] text-blue-400 font-medium">III</div>
                    <span className="text-zinc-400 text-[10px]">Castle</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-2 py-1 rounded">
                    <div className="w-5 h-5 rounded bg-purple-500/30 flex items-center justify-center text-[9px] text-purple-400 font-medium">IV</div>
                    <span className="text-zinc-400 text-[10px]">Imperial</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Coming Soon - Expanded */}
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 flex-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold text-zinc-500 text-sm">
                  +
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">More Games Coming</h3>
                  <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider">On Our Roadmap</span>
                </div>
              </div>

              <p className="text-zinc-400 text-sm mb-4">
                Same AI engine works across genres. We&apos;re adding new games based on community requests.
              </p>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                  <span className="text-sm text-zinc-300 font-medium">Valorant</span>
                  <p className="text-[10px] text-zinc-600 mt-0.5">Tactical FPS</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                  <span className="text-sm text-zinc-300 font-medium">Dota 2</span>
                  <p className="text-[10px] text-zinc-600 mt-0.5">MOBA</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                  <span className="text-sm text-zinc-300 font-medium">League of Legends</span>
                  <p className="text-[10px] text-zinc-600 mt-0.5">MOBA</p>
                </div>
                <div className="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                  <span className="text-sm text-zinc-300 font-medium">Rocket League</span>
                  <p className="text-[10px] text-zinc-600 mt-0.5">Sports</p>
                </div>
              </div>

              <p className="text-xs text-zinc-600 mt-4 text-center">
                Request a game on our <span className="text-zinc-400">GitHub</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
