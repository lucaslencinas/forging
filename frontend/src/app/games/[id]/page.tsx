"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { VideoAnalysisResults } from "@/components/VideoAnalysisResults";
import { ChatSidebar } from "@/components/ChatSidebar";
import type { components } from "@/types/api";

type AnalysisDetailResponse = components["schemas"]["AnalysisDetailResponse"];
type AnalysisStatusResponse = components["schemas"]["AnalysisStatusResponse"];

// Stage display names
const STAGE_LABELS: Record<string, string> = {
  parsing_demo: "Parsing demo file...",
  uploading_video: "Uploading video to AI...",
  detecting_rounds: "Detecting rounds in video...",
  analyzing: "Analyzing your gameplay...",
  validating: "Verifying tips...",
  generating_thumbnail: "Creating thumbnail...",
  generating_audio: "Generating voice feedback...",
};

// Stage progress percentages
const STAGE_PROGRESS: Record<string, number> = {
  parsing_demo: 10,
  uploading_video: 25,
  detecting_rounds: 35,
  analyzing: 60,
  validating: 80,
  generating_thumbnail: 90,
  generating_audio: 95,
};

// Adaptive polling intervals - poll less frequently early, more often later
function getPollingInterval(elapsedMs: number): number {
  if (elapsedMs < 90000) return 15000;     // First 1.5 min: every 15s (analyzing stage)
  if (elapsedMs < 180000) return 8000;     // 1.5-3 min: every 8s (validating stage)
  return 3000;                              // After 3 min: every 3s (should be finishing)
}

// AI Thinking placeholder for coaching tips
function AIThinkingPlaceholder({ stage }: { stage: string | null }) {
  const stageLabel = stage ? STAGE_LABELS[stage] || stage : "Starting analysis...";
  const progress = stage ? STAGE_PROGRESS[stage] || 50 : 5;

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
              {stageLabel}
            </p>

            {/* Progress bar */}
            <div className="mt-4 w-full bg-zinc-700 rounded-full h-2">
              <div
                className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="mt-3 flex items-center gap-2">
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

const DEFAULT_CHAT_WIDTH = 384;

export default function SharedGamePage() {
  const params = useParams();
  const id = params.id as string;

  const [analysis, setAnalysis] = useState<AnalysisDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stage, setStage] = useState<string | null>(null);
  // Stable video URL - only set once to prevent video reloading during polling
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [chatWidth, setChatWidth] = useState(DEFAULT_CHAT_WIDTH);
  const startTimeRef = useRef<number>(Date.now());

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  // Fetch full analysis data (only when complete or for initial load)
  const fetchAnalysis = useCallback(async () => {
    try {
      const response = await fetch(`${apiUrl}/api/analysis/${id}`);

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("Analysis not found");
        }
        throw new Error(`Failed to load analysis: ${response.statusText}`);
      }

      const data: AnalysisDetailResponse = await response.json();
      setAnalysis(data);

      // Only set video URL once to prevent video reloading during polling
      if (data.video_signed_url) {
        setVideoUrl((prev) => prev || data.video_signed_url);
      }

      return data.status !== "processing";
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      return true; // Stop polling on error
    } finally {
      setLoading(false);
    }
  }, [id, apiUrl]);

  // Poll status endpoint (lightweight)
  const pollStatus = useCallback(async (): Promise<boolean> => {
    try {
      console.log(`[polling] Fetching status for ${id}...`);
      const response = await fetch(`${apiUrl}/api/analysis/${id}/status`);

      if (!response.ok) {
        if (response.status === 404) {
          setError("Analysis not found");
          return true;
        }
        console.log(`[polling] Non-OK response: ${response.status}`);
        return false; // Continue polling on other errors
      }

      const data: AnalysisStatusResponse = await response.json();
      console.log(`[polling] Status: ${data.status}, Stage: ${data.stage}`);
      setStage(data.stage || null);

      if (data.status === "complete") {
        console.log(`[polling] Complete! Fetching full analysis...`);
        // Fetch full analysis data
        await fetchAnalysis();
        return true;
      }

      if (data.status === "error") {
        console.log(`[polling] Error: ${data.error}`);
        setError(data.error || "Analysis failed");
        return true;
      }

      console.log(`[polling] Still processing, will poll again...`);
      return false; // Continue polling
    } catch (err) {
      console.log(`[polling] Network error:`, err);
      return false; // Continue polling on network errors
    }
  }, [id, apiUrl, fetchAnalysis]);

  useEffect(() => {
    if (!id) return;

    let timeoutId: NodeJS.Timeout | null = null;
    let cancelled = false;

    async function startPolling() {
      console.log(`[polling] Starting polling for ${id}`);
      // Initial fetch to get video URL and current state
      const isComplete = await fetchAnalysis();
      console.log(`[polling] Initial fetch complete, isComplete: ${isComplete}`);

      if (isComplete || cancelled) {
        console.log(`[polling] Stopping - isComplete: ${isComplete}, cancelled: ${cancelled}`);
        return;
      }

      // Start adaptive polling using status endpoint
      async function poll() {
        if (cancelled) {
          console.log(`[polling] Cancelled, stopping`);
          return;
        }

        const done = await pollStatus();
        if (done || cancelled) {
          console.log(`[polling] Done or cancelled, stopping`);
          return;
        }

        const elapsed = Date.now() - startTimeRef.current;
        const interval = getPollingInterval(elapsed);
        console.log(`[polling] Scheduling next poll in ${interval}ms (elapsed: ${elapsed}ms)`);
        timeoutId = setTimeout(poll, interval);
      }

      poll();
    }

    startPolling();

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [id, fetchAnalysis, pollStatus]);

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
      <header className="border-b border-zinc-800 px-6 py-4 fixed top-0 left-0 right-0 z-30 bg-zinc-900/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between lg:transition-all" style={{ paddingRight: !isProcessing ? `${chatWidth}px` : undefined }}>
          <Link href="/" className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Forging</span>
          </Link>
          <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-12 pt-24">
        <div className="space-y-6 lg:transition-all" style={{ marginRight: !isProcessing ? `${chatWidth}px` : undefined }}>
          {/* Title and Summary */}
          {analysis.title && (
            <div>
              <h1 className="text-3xl font-bold text-zinc-100">
                {analysis.title}
              </h1>
              {/* Summary text as subtitle */}
              {analysis.summary_text && (
                <p className="mt-2 text-lg text-zinc-400">
                  {analysis.summary_text}
                </p>
              )}
            </div>
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
                  {videoUrl ? (
                    <video
                      className="w-full rounded-xl"
                      controls
                      src={videoUrl}
                    />
                  ) : (
                    <div className="aspect-video rounded-xl bg-zinc-800 flex items-center justify-center">
                      <p className="text-zinc-500">Loading video...</p>
                    </div>
                  )}
                </div>
                <AIThinkingPlaceholder stage={stage} />
              </div>
            </>
          ) : (
            <>
              {/* Convert AnalysisDetailResponse to VideoAnalysisResults format */}
              <VideoAnalysisResults
                analysis={{
                  game_type: analysis.game_type,
                  tips: analysis.tips,
                  game_summary: analysis.game_summary || undefined,
                  model_used: analysis.model_used || "",
                  provider: analysis.provider || "",
                  cs2_content: analysis.cs2_content,
                  aoe2_content: analysis.aoe2_content,
                }}
                videoUrl={videoUrl || analysis.video_signed_url}
                audioUrls={analysis.audio_urls || []}
              />
            </>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center text-sm text-zinc-500 lg:transition-all" style={{ paddingRight: !isProcessing ? `${chatWidth}px` : undefined }}>
        <p>Built for the Gemini 3 Hackathon</p>
      </footer>

      {/* Chat Sidebar - always visible on desktop, collapsible on mobile */}
      {!isProcessing && analysis && (
        <ChatSidebar analysisId={id} gameType={analysis.game_type} onWidthChange={setChatWidth} />
      )}
    </div>
  );
}
