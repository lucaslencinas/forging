"use client";

import { useState, useEffect } from "react";
import { GameLayout } from "./GameLayout";

interface AnalysisPendingViewProps {
  gameType: "aoe2" | "cs2";
  stage: string;
  videoUrl?: string;
  posterUrl?: string;
}

const STAGE_LABELS: Record<string, string> = {
  parsing_demo: "Parsing replay data...",
  downloading_video: "Downloading video...",
  uploading_video: "Uploading video to Gemini...",
  analyzing: "AI is analyzing your gameplay...",
  generating_thumbnail: "Generating thumbnail...",
  generating_audio: "Generating audio...",
};

function formatStage(stage: string): string {
  return STAGE_LABELS[stage] || stage;
}

// Hardcoded tips to show while waiting
const LOADING_TIPS: Record<"aoe2" | "cs2", string[]> = {
  aoe2: [
    "Keep your Town Center producing villagers constantly in the early game",
    "Scout your opponent's base to identify their strategy early",
    "Research Loom before sending villagers to dangerous areas",
    "Use control groups to manage multiple production buildings",
    "Don't forget to research economy upgrades at the Mill and Lumber Camp",
    "Walling can buy you time against early aggression",
    "Keep your army composition balanced - don't go all-in on one unit type",
    "Monks are extremely cost-effective if you can keep them alive",
    "Always have villagers queued - idle Town Centers lose you the game",
    "Castle Age timing is crucial - aim for sub-17 minutes in most games",
  ],
  cs2: [
    "Always aim for the head - headshots deal significantly more damage",
    "Learn smoke and flash lineups for key positions on each map",
    "Don't run and shoot - stop moving before firing for accuracy",
    "Communicate enemy positions with your team using callouts",
    "Manage your economy - sometimes a full save is better than a force buy",
    "Use utility to clear common angles before peeking",
    "Crosshair placement is key - keep it at head level",
    "Trade kills effectively - don't peek alone when you can trade",
    "Learn spray patterns for the weapons you use most",
    "Play for trades on retakes - don't just run in one by one",
  ],
};

export function AnalysisPendingView({
  gameType,
  stage,
  videoUrl,
  posterUrl,
}: AnalysisPendingViewProps) {
  const [currentTipIndex, setCurrentTipIndex] = useState(0);
  const tips = LOADING_TIPS[gameType];

  // Rotate tips every 4 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTipIndex((prev) => (prev + 1) % tips.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [tips.length]);

  return (
    <GameLayout gameType={gameType}>
      <div className="col-span-12 flex flex-col items-center justify-center min-h-[80vh] px-6 pt-16">
        {/* Main loading card */}
        <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-8 text-center space-y-6">
          {/* Spinner */}
          <div className="flex justify-center">
            <div className="w-12 h-12 rounded-full border-4 border-amber-500/20 border-t-amber-500 animate-spin" />
          </div>

          {/* Status */}
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-white">
              Analyzing Your Gameplay
            </h2>
            <p className="text-zinc-400 text-sm">{formatStage(stage)}</p>
            <p className="text-zinc-500 text-xs">
              This usually takes 3-5 minutes
            </p>
          </div>

          {/* Video preview (blurred) */}
          {(videoUrl || posterUrl) && (
            <div className="relative rounded-xl overflow-hidden aspect-video max-w-md mx-auto">
              {posterUrl ? (
                <img
                  src={posterUrl}
                  alt="Video thumbnail"
                  className="w-full h-full object-cover blur-sm opacity-50"
                />
              ) : (
                <video
                  src={videoUrl}
                  className="w-full h-full object-cover blur-sm opacity-50"
                  muted
                  playsInline
                />
              )}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                <span className="text-zinc-400 text-sm">
                  Video will be available when analysis completes
                </span>
              </div>
            </div>
          )}

          {/* Rotating tip */}
          <div className="border-t border-white/10 pt-6">
            <p className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
              Tip while you wait
            </p>
            <p
              key={currentTipIndex}
              className="text-amber-400 text-sm animate-in fade-in duration-500"
            >
              {tips[currentTipIndex]}
            </p>
          </div>
        </div>
      </div>
    </GameLayout>
  );
}
