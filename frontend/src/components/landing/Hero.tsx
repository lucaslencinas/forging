import Link from "next/link";

export function Hero() {
  return (
    <section className="relative pt-32 pb-20 px-6">
      <div className="max-w-5xl mx-auto text-center">
        <h1 className="text-6xl md:text-8xl font-bold tracking-tighter bg-gradient-to-br from-white via-white to-white/40 bg-clip-text text-transparent pb-4">
          Master your
          <br />
          gameplay.
        </h1>
        <p className="mt-6 text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed">
          Forging analyzes your replays with military-grade precision. 
          Stop guessing why you lost. Start winning.
        </p>
        
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/new"
            className="h-12 px-8 rounded-full bg-white text-black font-semibold hover:bg-zinc-200 transition-colors flex items-center justify-center"
          >
            Analyze Your Game
          </Link>
          <button className="h-12 px-8 rounded-full bg-transparent border border-zinc-800 text-zinc-300 font-medium hover:bg-white/5 transition-colors">
            View Demo
          </button>
        </div>
      </div>
    </section>
  );
}
