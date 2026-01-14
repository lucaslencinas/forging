"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { VideoAnalysisResults } from "@/components/VideoAnalysisResults";
import type { components } from "@/types/api";

type AnalysisDetailResponse = components["schemas"]["AnalysisDetailResponse"];

export default function SharedGamePage() {
  const params = useParams();
  const id = params.id as string;

  const [analysis, setAnalysis] = useState<AnalysisDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAnalysis() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
        const response = await fetch(`${apiUrl}/api/analysis/${id}`);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error("Analysis not found");
          }
          throw new Error(`Failed to load analysis: ${response.statusText}`);
        }

        const data: AnalysisDetailResponse = await response.json();
        setAnalysis(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      fetchAnalysis();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
        <header className="border-b border-zinc-800 px-6 py-4">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <Link href="/" className="text-2xl font-bold tracking-tight">
              <span className="text-orange-500">Forging</span>
            </Link>
            <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-12">
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 animate-spin text-orange-500"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <p className="mt-4 text-zinc-400">Loading analysis...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
        <header className="border-b border-zinc-800 px-6 py-4">
          <div className="mx-auto flex max-w-6xl items-center justify-between">
            <Link href="/" className="text-2xl font-bold tracking-tight">
              <span className="text-orange-500">Forging</span>
            </Link>
            <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-12">
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-center">
            <p className="text-red-400">{error}</p>
            <Link
              href="/"
              className="mt-4 inline-block rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              Go Home
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <a href="/" className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Forging</span>
          </a>
          <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        <div className="space-y-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
          >
            ← Analyze Your Own Game
          </Link>

          {/* Title */}
          {analysis.title && (
            <h1 className="text-3xl font-bold text-zinc-100">{analysis.title}</h1>
          )}

          {/* Convert AnalysisDetailResponse to VideoAnalysisResults format */}
          <VideoAnalysisResults
            analysis={{
              video_object_name: "", // Not needed for display
              duration_seconds: 0,
              tips: analysis.tips,
              game_summary: analysis.game_summary || undefined,
              model_used: analysis.model_used,
              provider: analysis.provider,
            }}
            videoUrl={analysis.video_signed_url}
          />
        </div>
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center text-sm text-zinc-500">
        <p>Built for the Gemini 3 Hackathon</p>
      </footer>
    </div>
  );
}
