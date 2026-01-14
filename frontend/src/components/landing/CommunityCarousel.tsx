"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { components } from "@/types/api";

type AnalysisListItem = components["schemas"]["AnalysisListItem"];

const gameIcons: Record<string, string> = {
  aoe2: "🏰",
  cs2: "🎯",
};

export function CommunityCarousel() {
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) {
    return (
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
            Community Analyses
          </h2>
          <p className="mt-4 text-center text-zinc-400">
            See what others are learning
          </p>
          <div className="mt-12 flex justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent" />
          </div>
        </div>
      </section>
    );
  }

  if (analyses.length === 0) {
    return (
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
            Community Analyses
          </h2>
          <p className="mt-4 text-center text-zinc-400">
            Be the first to share your analysis!
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              href="/new"
              className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              Create Analysis
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="px-6 py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center text-2xl font-bold text-white sm:text-3xl">
          Community Analyses
        </h2>
        <p className="mt-4 text-center text-zinc-400">
          See what others are learning
        </p>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {analyses.map((analysis) => (
            <Link
              key={analysis.id}
              href={`/games/${analysis.id}`}
              className="group rounded-xl border border-zinc-700 bg-zinc-800/50 p-4 transition-all hover:border-zinc-600 hover:bg-zinc-800"
            >
              {/* Thumbnail placeholder */}
              <div className="aspect-video rounded-lg bg-zinc-700/50 flex items-center justify-center text-4xl">
                {gameIcons[analysis.game_type] || "🎮"}
              </div>

              <div className="mt-4">
                <h3 className="font-medium text-white group-hover:text-orange-400 transition-colors truncate">
                  {analysis.title}
                </h3>
                {analysis.creator_name && (
                  <p className="mt-1 text-sm text-zinc-500">
                    by {analysis.creator_name}
                  </p>
                )}
                <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
                  <span className="uppercase">{analysis.game_type}</span>
                  <span>{analysis.tips_count} tips</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
