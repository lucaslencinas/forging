"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { VideoAnalysisResults } from "@/components/VideoAnalysisResults";
import type { components } from "@/types/api";

type AnalysisDetailResponse = components["schemas"]["AnalysisDetailResponse"];

// AI Thinking placeholder for coaching tips
function AIThinkingPlaceholder() {
  return (
    <div className="space-y-4">
      <h3 className="flex items-center gap-2 text-xl font-semibold text-zinc-100">
        <span>📋</span> Coaching Tips
        <span className="text-sm font-normal text-zinc-500">(analyzing...)</span>
      </h3>

      {/* AI thinking card */}
      <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-500/20">
            <svg
              className="h-6 w-6 animate-pulse text-orange-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-medium text-orange-400">
              AI Coach is analyzing your gameplay...
            </h4>
            <p className="mt-1 text-sm text-zinc-400">
              Watching your video and identifying key moments for improvement.
              This usually takes 2-5 minutes.
            </p>
            <div className="mt-4 flex items-center gap-2">
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: "0ms" }} />
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: "150ms" }} />
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-orange-400" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        </div>
      </div>

      {/* Placeholder tip skeletons */}
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-xl border border-zinc-700/50 bg-zinc-800/30 p-4 opacity-50"
        >
          <div className="flex items-start gap-4">
            <div className="h-6 w-14 rounded bg-zinc-700/50" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-16 rounded bg-zinc-700/50" />
              <div className="h-3 w-full rounded bg-zinc-700/50" />
              <div className="h-3 w-3/4 rounded bg-zinc-700/50" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SharedGamePage() {
  const params = useParams();
  const id = params.id as string;

  const [analysis, setAnalysis] = useState<AnalysisDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async () => {
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

      // If still processing, continue polling
      if (data.status === "processing") {
        return false; // Not complete
      }

      return true; // Complete or error
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      return true; // Stop polling on error
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;

    let pollInterval: NodeJS.Timeout | null = null;

    async function startPolling() {
      const isComplete = await fetchAnalysis();

      if (!isComplete) {
        // Poll every 5 seconds while processing
        pollInterval = setInterval(async () => {
          const complete = await fetchAnalysis();
          if (complete && pollInterval) {
            clearInterval(pollInterval);
          }
        }, 5000);
      }
    }

    startPolling();

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [id, fetchAnalysis]);

  // Initial loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
        <header className="border-b border-zinc-800 px-6 py-4">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <Link href="/" className="text-2xl font-bold tracking-tight">
              <span className="text-orange-500">Forging</span>
            </Link>
            <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-12">
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

  // Error state
  if (error || (analysis && analysis.status === "error")) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
        <header className="border-b border-zinc-800 px-6 py-4">
          <div className="mx-auto flex max-w-7xl items-center justify-between">
            <Link href="/" className="text-2xl font-bold tracking-tight">
              <span className="text-orange-500">Forging</span>
            </Link>
            <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-12">
          <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-center">
            <p className="text-red-400">
              {error || analysis?.error || "Analysis failed"}
            </p>
            <Link
              href="/new"
              className="mt-4 inline-block rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              Try Again
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (!analysis) {
    return null;
  }

  // Processing state - show skeleton with status
  const isProcessing = analysis.status === "processing";

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <Link href="/" className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Forging</span>
          </Link>
          <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-12">
        <div className="space-y-6">
          <Link
            href="/new"
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
          >
            ← Analyze Your Own Game
          </Link>

          {/* Title */}
          {analysis.title && (
            <h1 className="text-3xl font-bold text-zinc-100">
              {analysis.title}
            </h1>
          )}

          {/* Game metadata - show even during processing */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-400">
            {/* Game type badge */}
            <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs font-medium uppercase">
              {analysis.game_type}
            </span>

            {/* Players */}
            {analysis.players && analysis.players.length > 0 && (
              <span>
                {analysis.players.slice(0, 2).join(" vs ")}
                {analysis.players.length > 2 && ` +${analysis.players.length - 2}`}
              </span>
            )}

            {/* Map */}
            {analysis.map && (
              <span className="flex items-center gap-1">
                <span className="text-zinc-500">Map:</span> {analysis.map}
              </span>
            )}

            {/* Duration */}
            {analysis.duration && (
              <span className="flex items-center gap-1">
                <span className="text-zinc-500">Duration:</span> {analysis.duration}
              </span>
            )}

            {/* Tips count - show processing state or actual count */}
            {isProcessing ? (
              <span className="flex items-center gap-1 text-orange-400">
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                analyzing...
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <span className="text-orange-400 font-medium">{analysis.tips_count}</span> coaching tips
              </span>
            )}
          </div>

          {isProcessing ? (
            <>
              {/* Video player - show during processing */}
              <div className="grid gap-6 lg:grid-cols-[1fr,400px]">
                <div>
                  <h2 className="mb-4 text-2xl font-bold text-zinc-100">Video Analysis</h2>
                  {analysis.video_signed_url ? (
                    <video
                      className="w-full rounded-xl"
                      controls
                      src={analysis.video_signed_url}
                    />
                  ) : (
                    <div className="aspect-video rounded-xl bg-zinc-800 flex items-center justify-center">
                      <p className="text-zinc-500">Loading video...</p>
                    </div>
                  )}
                </div>
                <AIThinkingPlaceholder />
              </div>
            </>
          ) : (
            <>
              {/* Convert AnalysisDetailResponse to VideoAnalysisResults format */}
              <VideoAnalysisResults
                analysis={{
                  video_object_name: "", // Not needed for display
                  duration_seconds: 0,
                  tips: analysis.tips,
                  game_summary: analysis.game_summary || undefined,
                  model_used: analysis.model_used || "",
                  provider: analysis.provider || "",
                }}
                videoUrl={analysis.video_signed_url}
                audioUrls={analysis.audio_urls || []}
              />
            </>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center text-sm text-zinc-500">
        <p>Built for the Gemini 3 Hackathon</p>
      </footer>
    </div>
  );
}
