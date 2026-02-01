import Link from "next/link";

export function Hero() {
  return (
    <section className="relative overflow-hidden px-6 py-24 sm:py-32">
      {/* Subtle gradient background with purple/blue accents */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-zinc-900 via-zinc-900 to-purple-950/30" />
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-orange-900/20 via-transparent to-transparent" />
      <div className="absolute top-0 right-0 w-1/2 h-1/2 -z-10 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent" />

      <div className="mx-auto max-w-4xl text-center">
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
          AI-Powered Game Coaching
        </h1>
        <p className="mt-6 text-lg leading-8 text-zinc-400">
          Upload your gameplay video and get personalized, timestamped coaching tips in minutes.
          Improve faster with insights from advanced AI analysis.
        </p>
        <div className="mt-10 flex items-center justify-center gap-x-6">
          <Link
            href="/new"
            className="rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 px-6 py-3 text-lg font-semibold text-white shadow-lg transition-all hover:from-orange-600 hover:to-amber-600 hover:shadow-orange-500/25"
          >
            Analyze Your Game
          </Link>
        </div>
      </div>
    </section>
  );
}
