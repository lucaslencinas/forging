"use client";

import { useState } from "react";
import { GameSelector } from "@/components/GameSelector";
import { FileUpload } from "@/components/FileUpload";
import { AnalysisResults } from "@/components/AnalysisResults";
import type { components } from "@/types/api";

type GameType = "aoe2" | "cs2" | null;
type AnalysisState = "idle" | "uploading" | "analyzing" | "complete" | "error";
type AnalysisResponse = components["schemas"]["AnalysisResponse"];

export default function Home() {
  const [selectedGame, setSelectedGame] = useState<GameType>(null);
  const [analysisState, setAnalysisState] = useState<AnalysisState>("idle");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
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

  const handleReset = () => {
    setSelectedGame(null);
    setAnalysisState("idle");
    setAnalysisResult(null);
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
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-orange-500">Forging</span>
          </h1>
          <p className="text-sm text-zinc-400">AI-Powered Game Coach</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        {(analysisState === "complete" || ((analysisState === "uploading" || analysisState === "analyzing") && analysisResult)) && analysisResult ? (
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
                isLoading={analysisState === "uploading" || analysisState === "analyzing"}
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
