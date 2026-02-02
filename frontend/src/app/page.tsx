import Link from "next/link";
import {
  Hero,
  SupportedGames,
  HowItWorks,
  Features,
  Roadmap,
  CommunityCarousel,
  Footer,
} from "@/components/landing";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-900 to-purple-950/20 text-white">
      <header className="sticky top-0 z-50 border-b border-zinc-800/50 px-6 py-4 backdrop-blur-md bg-zinc-900/90">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <span className="text-2xl font-bold tracking-tight text-orange-500">Forging</span>
            <span className="hidden sm:block text-xs text-zinc-500 border-l border-zinc-700 pl-3">AI-Powered Game Coaching</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/new"
              className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-orange-700"
            >
              Analyze Your Game
            </Link>
          </div>
        </div>
      </header>
      <main>
        <Hero />
        <SupportedGames />
        <HowItWorks />
        <Features />
        <Roadmap />
        <CommunityCarousel />
      </main>

      <Footer />
    </div>
  );
}
