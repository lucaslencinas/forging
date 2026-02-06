"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface HeaderProps {
  showCTAOnScroll?: boolean;
  transparentUntilScroll?: boolean;
}

export function Header({ showCTAOnScroll = false, transparentUntilScroll = false }: HeaderProps) {
  const [showCTA, setShowCTA] = useState(!showCTAOnScroll);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      // Show CTA when scrolled past ~400px (roughly when hero button goes out of view)
      if (showCTAOnScroll) {
        const scrollThreshold = 400;
        setShowCTA(window.scrollY > scrollThreshold);
      }

      // Transition header background after scrolling 80px
      if (transparentUntilScroll) {
        setIsScrolled(window.scrollY > 80);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll(); // Check initial position

    return () => window.removeEventListener("scroll", handleScroll);
  }, [showCTAOnScroll, transparentUntilScroll]);

  const headerBg = transparentUntilScroll
    ? isScrolled
      ? "bg-zinc-950/95 backdrop-blur-md border-b border-zinc-800/50"
      : "bg-transparent border-b border-transparent"
    : "bg-zinc-900/90 backdrop-blur-md border-b border-zinc-800/50";

  return (
    <header className={`sticky top-0 z-50 px-6 py-4 transition-all duration-300 ${headerBg}`}>
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <span className="text-2xl font-bold tracking-tighter text-amber-500">FORGING</span>
          <span className="hidden sm:block text-xs text-zinc-500 border-l border-zinc-700 pl-3">
            AI-Powered Game Coaching
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <Link
            href="/new"
            className={`h-10 px-6 rounded-full bg-white text-black font-semibold hover:bg-zinc-200 transition-all flex items-center justify-center text-sm ${
              showCTA ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2 pointer-events-none"
            }`}
          >
            Analyze Your Game
          </Link>
        </div>
      </div>
    </header>
  );
}
