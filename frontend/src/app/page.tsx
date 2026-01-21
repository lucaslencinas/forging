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
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/" className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Forging</span>
          </Link>
          <div className="flex items-center gap-4">
            <a
              href="https://github.com/lucaslencinas/forging"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-zinc-400 transition-colors hover:text-white"
            >
              GitHub
            </a>
            <Link
              href="/new"
              className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-orange-700"
            >
              Try It Free
            </Link>
          </div>
        </div>
      </header>

      {/* Main content */}
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
