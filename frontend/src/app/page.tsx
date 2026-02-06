
import {
  Hero,
  SupportedGames,
  HowItWorks,
  Features,
  Roadmap,
  CommunityCarousel,
  Footer,
} from "@/components/landing";

import { Header } from "@/components/layout/Header";
import { Background } from "@/components/layout/Background";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white relative">
      <Background />

      <div className="relative z-10">
        <Header showCTAOnScroll transparentUntilScroll />
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
    </div>
  );
}
