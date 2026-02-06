"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import type { components } from "@/types/api";

type AnalysisListItem = components["schemas"]["AnalysisListItem"];

const gamePlaceholders: Record<string, string> = {
  aoe2: "/game-placeholders/aoe2.svg",
  cs2: "/game-placeholders/cs2.svg",
};


export function CommunityCarousel() {
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  useEffect(() => {
    async function fetchAnalyses() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
        const response = await fetch(`${apiUrl}/api/analyses?limit=12`);
        if (response.ok) {
          const data = await response.json();
          setAnalyses(data.analyses || []);
        }
      } catch (error) {
        console.error("Failed to fetch analyses:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchAnalyses();
  }, []);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScroll();
    const ref = scrollRef.current;
    if (ref) {
      ref.addEventListener("scroll", checkScroll);
      return () => ref.removeEventListener("scroll", checkScroll);
    }
  }, [analyses]);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const scrollAmount = 320; // Card width + gap
      scrollRef.current.scrollBy({
        left: direction === "left" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  if (loading) {
    return (
      <section className="py-24 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
              Community Analyses
            </h2>
            <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
              See what others are learning from their gameplay
            </p>
          </div>
          <div className="flex justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
          </div>
        </div>
      </section>
    );
  }

  if (analyses.length === 0) {
    return (
      <section className="py-24 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
              Community Analyses
            </h2>
            <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
              Be the first to share your gameplay analysis!
            </p>
          </div>
          <div className="flex justify-center">
            <Link
              href="/new"
              className="group inline-flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3 font-semibold text-black transition-all hover:bg-amber-400 hover:gap-3"
            >
              Create Analysis
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="py-24 relative">
      {/* Gradient overlays - positioned relative to viewport edges */}
      <div className={`absolute left-0 top-0 bottom-0 w-24 bg-gradient-to-r from-zinc-950 to-transparent z-[5] pointer-events-none transition-opacity ${canScrollLeft ? "opacity-100" : "opacity-0"}`} />
      <div className={`absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-zinc-950 to-transparent z-[5] pointer-events-none transition-opacity ${canScrollRight ? "opacity-100" : "opacity-0"}`} />

      <div className="mx-auto max-w-6xl px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-4">
            Community Analyses
          </h2>
          <p className="text-zinc-500 text-lg max-w-2xl mx-auto">
            See what others are learning from their gameplay
          </p>
        </div>

        {/* Carousel container */}
        <div className="relative">
          {/* Left scroll button */}
          <button
            onClick={() => scroll("left")}
            className={`absolute left-0 top-1/2 -translate-y-1/2 -translate-x-4 z-10 w-10 h-10 rounded-full bg-zinc-800 border border-white/10 flex items-center justify-center transition-all ${
              canScrollLeft
                ? "opacity-100 hover:bg-zinc-700 hover:border-white/20"
                : "opacity-0 pointer-events-none"
            }`}
            aria-label="Scroll left"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Right scroll button */}
          <button
            onClick={() => scroll("right")}
            className={`absolute right-0 top-1/2 -translate-y-1/2 translate-x-4 z-10 w-10 h-10 rounded-full bg-zinc-800 border border-white/10 flex items-center justify-center transition-all ${
              canScrollRight
                ? "opacity-100 hover:bg-zinc-700 hover:border-white/20"
                : "opacity-0 pointer-events-none"
            }`}
            aria-label="Scroll right"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>

          {/* Scrollable container */}
          <div
            ref={scrollRef}
            className="flex gap-4 overflow-x-auto scrollbar-hide pb-4 -mx-6 px-6 snap-x snap-mandatory"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
          >
            {analyses.map((analysis) => (
              <Link
                key={analysis.id}
                href={`/games/${analysis.id}`}
                className="group flex-shrink-0 w-72 rounded-2xl border border-white/10 bg-white/5 overflow-hidden hover:bg-white/[0.07] hover:border-white/20 transition-all snap-start"
              >
                {/* Thumbnail */}
                <div className="aspect-video bg-zinc-800 overflow-hidden relative">
                  {analysis.thumbnail_url ? (
                    <img
                      src={analysis.thumbnail_url}
                      alt={analysis.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = gamePlaceholders[analysis.game_type] || gamePlaceholders.aoe2;
                      }}
                    />
                  ) : (
                    <img
                      src={gamePlaceholders[analysis.game_type] || gamePlaceholders.aoe2}
                      alt={analysis.game_type}
                      className="w-full h-full object-cover"
                    />
                  )}

                  {/* Game type badge */}
                  <span
                    className={`absolute top-2 left-2 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest border backdrop-blur-sm ${
                      analysis.game_type === "aoe2"
                        ? "border-amber-500/50 text-amber-400 bg-amber-500/20"
                        : "border-blue-500/50 text-blue-400 bg-blue-500/20"
                    }`}
                  >
                    {analysis.game_type}
                  </span>

                  {/* Tips count badge */}
                  <span className="absolute top-2 right-2 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-black/60 text-amber-400 backdrop-blur-sm">
                    {analysis.tips_count} tips
                  </span>
                </div>

                <div className="p-4">
                  <h3 className="font-semibold text-white group-hover:text-amber-400 transition-colors truncate">
                    {analysis.title}
                  </h3>

                  {/* Player names */}
                  {analysis.players && analysis.players.length > 0 && (
                    <p className="mt-1 text-sm text-zinc-400 truncate">
                      {analysis.players.slice(0, 2).join(" vs ")}
                      {analysis.players.length > 2 && ` +${analysis.players.length - 2}`}
                    </p>
                  )}

                  {/* Map and duration */}
                  <div className="mt-2 flex items-center gap-2 text-xs text-zinc-500">
                    {analysis.map && (
                      <span className="truncate max-w-[100px]">{analysis.map}</span>
                    )}
                    {analysis.map && analysis.duration && <span className="text-zinc-600">·</span>}
                    {analysis.duration && <span>{analysis.duration}</span>}
                  </div>
                </div>
              </Link>
            ))}

            {/* "View All" card at end */}
            <Link
              href="/new"
              className="group flex-shrink-0 w-72 rounded-2xl border border-dashed border-white/10 bg-white/[0.02] overflow-hidden hover:bg-white/[0.05] hover:border-amber-500/30 transition-all snap-start flex flex-col items-center justify-center min-h-[280px]"
            >
              <div className="w-14 h-14 rounded-full bg-amber-500/10 flex items-center justify-center mb-4 group-hover:bg-amber-500/20 transition-colors">
                <svg className="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <span className="text-zinc-400 font-medium group-hover:text-amber-400 transition-colors">
                Analyze Your Game
              </span>
              <span className="text-xs text-zinc-600 mt-1">Upload a recording</span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
