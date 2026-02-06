"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { GameSelectorPortal } from "@/components/new/GameSelectorPortal";
import { FileUploadPortal } from "@/components/new/FileUploadPortal";
import { Background } from "@/components/layout/Background";
import type { components } from "@/types/api";

type GameType = "aoe2" | "cs2" | null;
type AnalysisState = "idle" | "video-analyzing" | "error";
type AnalysisStartResponse = components["schemas"]["AnalysisStartResponse"];

export default function NewAnalysisPageV2() {
  const router = useRouter();
  const [selectedGame, setSelectedGame] = useState<GameType>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [error, setError] = useState<string | null>(null);

  const handleVideoAnalyze = async (videoObjectName: string, replayFile: File | null, povPlayer: string | null) => {
    if (!selectedGame || !replayFile) return;

    setAnalysisState("video-analyzing");
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

      // Step 1: Upload replay file to GCS
      const uploadUrlResponse = await fetch(`${apiUrl}/api/replay/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: replayFile.name,
          content_type: "application/octet-stream",
          file_size: replayFile.size,
        }),
      });

      if (!uploadUrlResponse.ok) {
        const error = await uploadUrlResponse.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to get replay upload URL");
      }

      const { signed_url, object_name: replayObjectName } = await uploadUrlResponse.json();

      // Upload replay to GCS
      const uploadResponse = await fetch(signed_url, {
        method: "PUT",
        headers: { "Content-Type": "application/octet-stream" },
        body: replayFile,
      });

      if (!uploadResponse.ok) {
        throw new Error("Failed to upload replay file");
      }

      // Step 2: Start the analysis with both video and replay
      const response = await fetch(`${apiUrl}/api/analysis`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          video_object_name: videoObjectName,
          replay_object_name: replayObjectName,
          game_type: selectedGame,
          is_public: true,
          pov_player: povPlayer,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Analysis failed: ${response.statusText}`);
      }

      const result: AnalysisStartResponse = await response.json();

      // Redirect immediately to the analysis page (it will show skeleton while processing)
      router.push(`/games/${result.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setAnalysisState("error");
    }
  };

  const handleReset = () => {
    setSelectedGame(null);
    setAnalysisState("idle");
    setError(null);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white selection:bg-amber-500/30 font-sans overflow-x-hidden">
      <Background />

      <div className="relative z-10">
        <Header />

        {/* Content Container - positioned higher like home page */}
        <main className="min-h-[calc(100vh-80px)] flex flex-col items-center justify-start px-6 pt-16 md:pt-24 pb-12">

          {/* Title Block */}
          <div className="mb-10 text-center space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold tracking-tighter bg-gradient-to-br from-white via-white to-white/40 bg-clip-text text-transparent pb-2">
              Level up your <span className="italic">game</span>
            </h1>
            <p className="text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed">
              Upload your replay file and get AI-powered coaching feedback
            </p>
          </div>

          {/* Component Stage */}
          <div className="w-full max-w-5xl relative">
            <GameSelectorPortal
              selectedGame={selectedGame}
              onSelect={setSelectedGame}
            />

            {/* File Upload Stage */}
            {selectedGame && (
              <FileUploadPortal
                gameType={selectedGame}
                isLoading={analysisState === "video-analyzing"}
                onVideoAnalyze={handleVideoAnalyze}
              />
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-8 rounded-xl border border-red-500/50 bg-red-500/10 backdrop-blur-sm p-6 text-center">
                <p className="text-red-400 mb-4">{error}</p>
                <button
                  onClick={handleReset}
                  className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium transition-colors hover:bg-amber-700"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
