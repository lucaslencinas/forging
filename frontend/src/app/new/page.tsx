"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GameSelector } from "@/components/GameSelector";
import { FileUpload } from "@/components/FileUpload";
import type { components } from "@/types/api";

type GameType = "aoe2" | "cs2" | null;
type AnalysisState = "idle" | "video-analyzing" | "error";
type AnalysisStartResponse = components["schemas"]["AnalysisStartResponse"];

export default function Home() {
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
        <div className="space-y-12">
          {/* Hero Section */}
          <div className="text-center">
            <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">
              Level up your game
            </h2>
            <p className="mt-4 text-lg text-zinc-400">
              Upload your replay file and get AI-powered coaching feedback
            </p>
          </div>

          {/* Game Selection */}
          <GameSelector
            selectedGame={selectedGame}
            onSelect={setSelectedGame}
          />

          {/* File Upload */}
          {selectedGame && (
            <FileUpload
              gameType={selectedGame}
              onVideoAnalyze={handleVideoAnalyze}
              isLoading={analysisState === "video-analyzing"}
              loadingState={analysisState}
            />
          )}

          {/* Error Display */}
          {error && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={handleReset}
                className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium transition-colors hover:bg-orange-700"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center text-sm text-zinc-500">
        <p>Built for the Gemini 3 Hackathon</p>
      </footer>
    </div>
  );
}
