"use client";

import { useEffect, useState, useRef, useMemo, useCallback } from "react";
import { useParams } from "next/navigation";
import { GameLayout } from "@/components/games/GameLayout";
import { VideoPlayerV2, VideoPlayerV2Ref } from "@/components/games/VideoPlayerV2";
import { GameSidebar } from "@/components/games/GameSidebar";
import { TipsStreamV2 } from "@/components/games/TipsStreamV2";
import { AgeProgressionV2 } from "@/components/games/AgeProgressionV2";
import { RoundsProgressionV2 } from "@/components/games/RoundsProgressionV2";
import { AnalysisPendingView } from "@/components/games/AnalysisPendingView";
import type { components } from "@/types/api";

type AnalysisDetailResponse = components["schemas"]["AnalysisDetailResponse"];
type AnalysisStatusResponse = components["schemas"]["AnalysisStatusResponse"];

const DEFAULT_SIDEBAR_WIDTH = 384;
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function GameAnalysisPageV2() {
  const params = useParams();
  const id = params?.id as string;
  const [analysis, setAnalysis] = useState<AnalysisDetailResponse | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatusResponse | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_SIDEBAR_WIDTH);
  const [isDesktop, setIsDesktop] = useState(true);
  const [isPolling, setIsPolling] = useState(false);

  const videoRef = useRef<VideoPlayerV2Ref>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingInFlight = useRef(false);
  const hasEnteredAnalyzingStage = useRef(false);

  // Track screen size for responsive sidebar margin
  // Using 880px as breakpoint (approx lg - 150px) for better responsiveness
  const DESKTOP_BREAKPOINT = 880;
  useEffect(() => {
    const checkDesktop = () => setIsDesktop(window.innerWidth >= DESKTOP_BREAKPOINT);
    checkDesktop();
    window.addEventListener("resize", checkDesktop);
    return () => window.removeEventListener("resize", checkDesktop);
  }, []);

  // Fetch analysis data
  const fetchAnalysis = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/analysis/${id}`);
      if (res.ok) {
        const data: AnalysisDetailResponse = await res.json();
        setAnalysis(data);
        return data;
      }
    } catch (e) {
      console.error("Failed to fetch analysis", e);
    }
    return null;
  }, [id]);

  // Poll status endpoint
  const pollStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/analysis/${id}/status`);
      if (res.ok) {
        const data: AnalysisStatusResponse = await res.json();
        setAnalysisStatus(data);
        return data;
      }
    } catch (e) {
      console.error("Failed to poll status", e);
    }
    return null;
  }, [id]);

  // Keep stable ref to fetchAnalysis for polling effect
  const fetchAnalysisRef = useRef(fetchAnalysis);
  useEffect(() => {
    fetchAnalysisRef.current = fetchAnalysis;
  }, [fetchAnalysis]);

  // Initial fetch and setup polling if needed
  useEffect(() => {
    if (!id) return;

    const init = async () => {
      const data = await fetchAnalysis();
      if (data && (data.status === "pending" || data.status === "processing")) {
        // Start polling
        setIsPolling(true);
      }
    };
    init();

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [id, fetchAnalysis]);

  // Polling effect with dynamic interval
  // Fast polling (5s) for early stages, slower (15s) once analyzing starts
  const FAST_POLL_INTERVAL = 5000;
  const SLOW_POLL_INTERVAL = 15000;

  useEffect(() => {
    if (!isPolling || !id) return;

    const scheduleNextPoll = () => {
      const interval = hasEnteredAnalyzingStage.current ? SLOW_POLL_INTERVAL : FAST_POLL_INTERVAL;
      pollIntervalRef.current = setTimeout(poll, interval);
    };

    const poll = async () => {
      // Skip if already polling to prevent duplicate requests
      if (isPollingInFlight.current) return;
      isPollingInFlight.current = true;

      try {
        const status = await pollStatus();
        if (status) {
          // Check if we've entered the analyzing stage (or later)
          if (status.stage === "analyzing" || status.stage === "generating_thumbnail") {
            hasEnteredAnalyzingStage.current = true;
          }

          if (status.status === "complete") {
            // Stop polling and refetch full analysis
            setIsPolling(false);
            if (pollIntervalRef.current) {
              clearTimeout(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            // Use ref to avoid stale closure
            fetchAnalysisRef.current();
            return;
          } else if (status.status === "error") {
            setIsPolling(false);
            if (pollIntervalRef.current) {
              clearTimeout(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            // Refetch to get error message
            fetchAnalysisRef.current();
            return;
          }
        }
        // Schedule next poll
        scheduleNextPoll();
      } finally {
        isPollingInFlight.current = false;
      }
    };

    // Reset the analyzing stage flag when starting fresh
    hasEnteredAnalyzingStage.current = false;
    // Poll immediately
    poll();

    return () => {
      if (pollIntervalRef.current) {
        clearTimeout(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [isPolling, id, pollStatus]); // Removed fetchAnalysis dep - using ref instead

  const handleSeek = (seconds: number) => {
    videoRef.current?.seek(seconds);
  };

  const handleProgress = (seconds: number) => {
    setCurrentTime(seconds);
  };

  // Get tips near current time for floating display
  const nearbyTips = useMemo(() => {
    if (!analysis?.tips) return [];
    return analysis.tips.filter((t) => Math.abs(t.timestamp_seconds - currentTime) < 5);
  }, [analysis?.tips, currentTime]);

  // Show loading state
  if (!analysis) {
    return (
      <div className="h-screen w-screen bg-black flex items-center justify-center text-amber-500 text-sm animate-pulse">
        Loading analysis...
      </div>
    );
  }

  // Determine if we're still in early stages (before analyzing starts)
  const isEarlyStage =
    (analysis.status === "pending" || analysis.status === "processing") &&
    analysisStatus?.stage !== "analyzing" &&
    analysisStatus?.stage !== "generating_thumbnail" &&
    analysisStatus?.stage !== "generating_audio";

  // Show pending view only during early stages
  if (isEarlyStage) {
    return (
      <AnalysisPendingView
        gameType={analysis.game_type as "aoe2" | "cs2"}
        stage={analysisStatus?.stage || "Preparing analysis..."}
        videoUrl={analysis.video_signed_url}
        posterUrl={analysis.thumbnail_url ?? undefined}
      />
    );
  }

  // Analysis is in progress but past early stages - show normal page with loading state
  const isAnalyzing = analysis.status === "pending" || analysis.status === "processing";

  // Show error view if analysis failed
  if (analysis.status === "error") {
    return (
      <GameLayout gameType={analysis.game_type}>
        <div className="col-span-12 flex flex-col items-center justify-center min-h-[80vh] px-6 pt-16">
          <div className="w-full max-w-2xl rounded-2xl border border-red-500/20 bg-red-500/5 backdrop-blur-sm p-8 text-center space-y-6">
            {/* Error icon */}
            <div className="flex justify-center">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Error message */}
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-white">
                Analysis Failed
              </h2>
              <p className="text-zinc-400 text-sm">
                Something went wrong while analyzing your gameplay.
              </p>
              {analysis.error && (
                <p className="text-red-400 text-xs font-mono bg-red-500/10 rounded-lg p-3 mt-4 text-left overflow-auto max-h-32">
                  {analysis.error}
                </p>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-center gap-4 pt-4">
              <a
                href="/new"
                className="px-4 py-2 rounded-lg bg-amber-500 text-black font-medium hover:bg-amber-400 transition-colors"
              >
                Try Again
              </a>
              <a
                href="/"
                className="px-4 py-2 rounded-lg border border-white/20 text-white hover:bg-white/5 transition-colors"
              >
                Go Home
              </a>
            </div>
          </div>
        </div>
      </GameLayout>
    );
  }

  // Check if we have AoE2 age progression data
  const hasAgeProgression =
    analysis.game_type === "aoe2" &&
    analysis.aoe2_content?.players_timeline &&
    analysis.aoe2_content.players_timeline.length > 0;

  // Check if we have CS2 rounds data
  const hasRoundsProgression =
    analysis.game_type === "cs2" &&
    analysis.cs2_content?.rounds_timeline &&
    analysis.cs2_content.rounds_timeline.length > 0;

  return (
    <GameLayout gameType={analysis.game_type}>
      {/* Analyzing Banner */}
      {isAnalyzing && (
        <div className="fixed top-16 left-0 right-0 z-50 bg-amber-500/10 border-b border-amber-500/30 backdrop-blur-sm">
          <div
            className="px-4 py-2 flex items-center justify-center gap-3 text-sm"
            style={{ marginRight: isDesktop ? `${sidebarWidth}px` : '0px' }}
          >
            <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            <span className="text-amber-400 font-medium">
              {analysisStatus?.stage === "analyzing"
                ? "AI is analyzing your gameplay..."
                : analysisStatus?.stage === "generating_thumbnail"
                ? "Generating thumbnail..."
                : analysisStatus?.stage === "generating_audio"
                ? "Generating audio..."
                : "Processing..."}
            </span>
          </div>
        </div>
      )}

      {/* Main scrollable content area */}
      <div
        className="transition-all"
        style={{
          marginRight: isDesktop ? `${sidebarWidth}px` : '0px',
          paddingBottom: isDesktop ? '2rem' : '50vh',
          paddingTop: isAnalyzing ? '40px' : '0px'
        }}
      >
        {/* Title and Metadata Header - compact on mobile */}
        <div className="px-4 md:px-6 py-2 md:py-4 space-y-2 md:space-y-3 flex-shrink-0">
          {/* Title */}
          <h1 className="text-lg md:text-2xl lg:text-3xl font-bold tracking-tight bg-gradient-to-br from-white via-white to-white/40 bg-clip-text text-transparent">
            {analysis.title}
          </h1>

          {/* Summary text - hidden on very small screens */}
          {analysis.summary_text && (
            <p className="hidden sm:block text-sm text-zinc-500 leading-relaxed max-w-3xl">
              {analysis.summary_text}
            </p>
          )}

          {/* Metadata badges - compact on mobile */}
          <div className="flex flex-wrap items-center gap-2 md:gap-3 text-xs md:text-sm">
            {/* Game type badge */}
            <span
              className={`rounded-full px-2 md:px-3 py-0.5 md:py-1 text-[9px] md:text-[10px] font-bold uppercase tracking-widest border ${
                analysis.game_type === "aoe2"
                  ? "border-amber-500/50 text-amber-400 bg-amber-500/10"
                  : "border-blue-500/50 text-blue-400 bg-blue-500/10"
              }`}
            >
              {analysis.game_type}
            </span>

            {/* Players - different display for CS2 vs AoE2 */}
            {analysis.game_type === "cs2" && analysis.pov_player ? (
              <span className="text-zinc-400">
                <span className="text-amber-400 font-medium">{analysis.pov_player}</span>
                {analysis.cs2_content?.rounds_timeline && analysis.cs2_content.rounds_timeline.length > 0 && (
                  <span className="text-zinc-500">
                    {" "}({(() => {
                      const wins = analysis.cs2_content!.rounds_timeline.filter(r => r.status === "win").length;
                      const losses = analysis.cs2_content!.rounds_timeline.filter(r => r.status === "loss").length;
                      return `${wins}W - ${losses}L`;
                    })()})
                  </span>
                )}
              </span>
            ) : analysis.players && analysis.players.length > 0 && (
              <span className="text-zinc-400">
                {analysis.players.slice(0, 2).join(" vs ")}
                {analysis.players.length > 2 && ` +${analysis.players.length - 2}`}
              </span>
            )}

            {/* Map */}
            {analysis.map && (
              <span className="flex items-center gap-1.5 text-zinc-400">
                <span className="text-zinc-600">|</span>
                <span className="text-zinc-500">Map:</span> {analysis.map}
              </span>
            )}

            {/* Duration */}
            {analysis.duration && (
              <span className="flex items-center gap-1.5 text-zinc-400">
                <span className="text-zinc-600">|</span>
                <span className="text-zinc-500">Duration:</span> {analysis.duration}
              </span>
            )}

            {/* Tips count */}
            <span className="flex items-center gap-1.5">
              <span className="text-zinc-600">|</span>
              {isAnalyzing ? (
                <>
                  <span className="text-amber-400/50 font-semibold animate-pulse">...</span>
                  <span className="text-zinc-500">tips</span>
                </>
              ) : (
                <>
                  <span className="text-amber-400 font-semibold">
                    {analysis.tips_count}
                  </span>
                  <span className="text-zinc-500">tips</span>
                </>
              )}
            </span>
          </div>
        </div>

        {/* Video Player - full width with aspect ratio preserved */}
        <div className="w-full relative group bg-black">
          <div className="aspect-video max-h-[60vh] md:max-h-[70vh] w-full">
            <VideoPlayerV2
              ref={videoRef}
              videoUrl={analysis.video_signed_url}
              posterUrl={analysis.thumbnail_url ?? undefined}
              onProgress={handleProgress}
            />
          </div>

          {/* Floating Tips Overlay (HUD Notifications) */}
          <div className="absolute top-2 right-2 z-20 pointer-events-auto">
            <TipsStreamV2 tips={nearbyTips} />
          </div>
        </div>

        {/* Age Progression (for AoE2 - below video) */}
        {hasAgeProgression && (
          <div className="px-4 md:px-6 py-4">
            <AgeProgressionV2
              players={analysis.aoe2_content!.players_timeline}
              videoDuration={analysis.duration ?? undefined}
              povPlayerIndex={analysis.aoe2_content?.pov_player_index}
            />
          </div>
        )}

        {/* Rounds Progression (for CS2 - below video) */}
        {hasRoundsProgression && (
          <div className="px-4 md:px-6 py-4">
            <RoundsProgressionV2
              rounds={analysis.cs2_content!.rounds_timeline}
              currentTime={currentTime}
              onSeek={handleSeek}
            />
          </div>
        )}
      </div>

      {/* AREA B: Right Wing - Sidebar with AI Coach & Insights */}
      {/* Desktop: Fixed sidebar on right */}
      {isDesktop && (
        <div
          className="fixed right-0 top-16 bottom-0 bg-black/20 backdrop-blur-md"
          style={{ width: `${sidebarWidth}px` }}
        >
          <GameSidebar
            analysisId={id}
            gameType={analysis.game_type}
            tips={analysis.tips}
            currentTime={currentTime}
            onSeek={handleSeek}
            onWidthChange={setSidebarWidth}
            isAnalyzing={isAnalyzing}
          />
        </div>
      )}

      {/* Mobile: Sidebar at bottom, full width */}
      {!isDesktop && (
        <div className="fixed left-0 right-0 bottom-0 h-[50vh] bg-zinc-950 border-t border-white/10 z-40 rounded-t-xl overflow-hidden">
          <GameSidebar
            analysisId={id}
            gameType={analysis.game_type}
            tips={analysis.tips}
            currentTime={currentTime}
            onSeek={handleSeek}
            isAnalyzing={isAnalyzing}
          />
        </div>
      )}

    </GameLayout>
  );
}
