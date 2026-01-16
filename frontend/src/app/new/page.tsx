"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GameSelector } from "@/components/GameSelector";
import { FileUpload } from "@/components/FileUpload";
import { AnalysisResults } from "@/components/AnalysisResults";
import { VideoAnalysisResults } from "@/components/VideoAnalysisResults";
import type { components } from "@/types/api";

type GameType = "aoe2" | "cs2" | null;
type AnalysisState = "idle" | "uploading" | "analyzing" | "video-analyzing" | "complete" | "video-complete" | "error";
type AnalysisResponse = components["schemas"]["AnalysisResponse"];
type AnalysisStartResponse = components["schemas"]["AnalysisStartResponse"];
type VideoAnalysisResponse = components["schemas"]["VideoAnalysisResponse"];

export default function Home() {
  const router = useRouter();
  const [selectedGame, setSelectedGame] = useState<GameType>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [savedAnalysisResult, setSavedAnalysisResult] = useState<VideoAnalysisResponse | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastReplayFile, setLastReplayFile] = useState<File | null>(null);

  const handleAnalyze = async (replayFile: File, videoObjectName?: string) => {
    // Store the file for re-analysis
    setLastReplayFile(replayFile);
    if (!selectedGame) return;

    setAnalysisState("uploading");
    setError(null);

    try {
      const formData = new FormData();

      // Add replay file with correct field name
      if (selectedGame === "aoe2") {
        formData.append("replay", replayFile);
      } else {
        formData.append("demo", replayFile);
      }

      // Video is already uploaded to GCS, videoObjectName contains the path
      // This will be used in Milestone 3 for video analysis

      setAnalysisState("analyzing");

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const response = await fetch(`${apiUrl}/api/analyze/${selectedGame}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
      setAnalysisState("complete");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setAnalysisState("error");
    }
  };

  const handleVideoAnalyze = async (videoObjectName: string, replayFile: File | null, model?: string) => {
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
      const requestBody: {
        video_object_name: string;
        replay_object_name: string;
        game_type: string;
        model?: string;
        is_public: boolean;
      } = {
        video_object_name: videoObjectName,
        replay_object_name: replayObjectName,
        game_type: selectedGame,
        is_public: true,
      };

      if (model) {
        requestBody.model = model;
      }

      const response = await fetch(`${apiUrl}/api/analysis`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
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
    setAnalysisResult(null);
    setSavedAnalysisResult(null);
    setVideoUrl(null);
    setError(null);
    setLastReplayFile(null);
  };

  const handleReanalyze = async () => {
    if (lastReplayFile && selectedGame) {
      await handleAnalyze(lastReplayFile);
    }
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
        {/* Video Analysis Results */}
        {analysisState === "video-complete" && savedAnalysisResult && videoUrl ? (
          <div className="space-y-6">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              ← Back to Upload
            </button>
            <VideoAnalysisResults
              analysis={savedAnalysisResult}
              videoUrl={videoUrl}
            />
          </div>
        ) : (analysisState === "complete" || ((analysisState === "uploading" || analysisState === "analyzing") && analysisResult)) && analysisResult ? (
          <AnalysisResults
            result={analysisResult}
            onReset={handleReset}
            onReanalyze={handleReanalyze}
            isReanalyzing={analysisState === "uploading" || analysisState === "analyzing"}
          />
        ) : (
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
                onAnalyze={handleAnalyze}
                onVideoAnalyze={handleVideoAnalyze}
                isLoading={analysisState === "uploading" || analysisState === "analyzing" || analysisState === "video-analyzing"}
                loadingState={analysisState}
              />
            )}

            {/* Error Display */}
            {error && (
              <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-6 text-center">
                <p className="text-red-400 mb-4">{error}</p>
                {lastReplayFile && (
                  <button
                    onClick={handleReanalyze}
                    disabled={analysisState === "uploading" || analysisState === "analyzing"}
                    className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium transition-colors hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Try Again
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="border-t border-zinc-800 px-6 py-8 text-center text-sm text-zinc-500">
        <p>Built for the Gemini 3 Hackathon</p>
      </footer>
    </div>
  );
}
