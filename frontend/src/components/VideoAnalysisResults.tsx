"use client";

import { useRef, useState } from "react";
import { VideoPlayer, VideoPlayerRef } from "./VideoPlayer";
import { TimestampedTips } from "./TimestampedTips";
import type { components } from "@/types/api";

type VideoAnalysisResponse = components["schemas"]["VideoAnalysisResponse"];
type SavedAnalysisResponse = components["schemas"]["SavedAnalysisResponse"];
type GameSummary = components["schemas"]["GameSummary"];

interface VideoAnalysisResultsProps {
  analysis: VideoAnalysisResponse | SavedAnalysisResponse;
  videoUrl: string;
}

// Type guard to check if the analysis has share_url (SavedAnalysisResponse)
function hasSaveUrl(analysis: VideoAnalysisResponse | SavedAnalysisResponse): analysis is SavedAnalysisResponse {
  return 'share_url' in analysis;
}

export function VideoAnalysisResults({ analysis, videoUrl }: VideoAnalysisResultsProps) {
  const videoRef = useRef<VideoPlayerRef>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [copied, setCopied] = useState(false);

  const handleSeek = (seconds: number) => {
    videoRef.current?.seek(seconds);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleCopyShareUrl = async () => {
    if (hasSaveUrl(analysis)) {
      await navigator.clipboard.writeText(analysis.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const gameSummary = analysis.game_summary;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-zinc-100">Video Analysis</h2>
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <span className="rounded bg-zinc-800 px-2 py-1">
            {analysis.provider}
          </span>
          <span className="rounded bg-zinc-800 px-2 py-1">
            {analysis.model_used}
          </span>
        </div>
      </div>

      {/* Share URL */}
      {hasSaveUrl(analysis) && (
        <div className="flex items-center gap-3 rounded-xl border border-green-500/30 bg-green-500/10 p-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-green-400">Analysis saved!</p>
            <p className="text-xs text-zinc-400 mt-1">Share this link with others:</p>
            <p className="text-sm text-zinc-300 mt-1 font-mono truncate">{analysis.share_url}</p>
          </div>
          <button
            onClick={handleCopyShareUrl}
            className="shrink-0 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700"
          >
            {copied ? "Copied!" : "Copy Link"}
          </button>
        </div>
      )}

      {/* Game Summary (if replay was provided) */}
      {gameSummary && (
        <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="mb-3 text-sm font-medium text-zinc-400">Game Info</h3>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <span className="text-xs text-zinc-500">Map</span>
              <p className="text-sm text-zinc-200">{gameSummary.map}</p>
            </div>
            <div>
              <span className="text-xs text-zinc-500">Duration</span>
              <p className="text-sm text-zinc-200">{gameSummary.duration}</p>
            </div>
            <div>
              <span className="text-xs text-zinc-500">Players</span>
              <p className="text-sm text-zinc-200">
                {gameSummary.players?.map((p) => p.name).join(" vs ")}
              </p>
            </div>
            <div>
              <span className="text-xs text-zinc-500">Civilizations</span>
              <p className="text-sm text-zinc-200">
                {gameSummary.players?.map((p) => p.civilization).join(" vs ")}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error message (only VideoAnalysisResponse has error field) */}
      {'error' in analysis && analysis.error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <span className="font-medium">Analysis Error:</span> {analysis.error}
        </div>
      )}

      {/* Main content: Video + Tips */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Video Player */}
        <div className="space-y-2">
          <VideoPlayer
            ref={videoRef}
            src={videoUrl}
            onTimeUpdate={handleTimeUpdate}
            className="aspect-video"
          />
          <p className="text-center text-xs text-zinc-500">
            Click on a tip to jump to that moment in the video
          </p>
        </div>

        {/* Timestamped Tips */}
        <TimestampedTips
          tips={analysis.tips || []}
          currentTime={currentTime}
          onSeek={handleSeek}
        />
      </div>

      {/* Summary stats - dynamically show categories present */}
      {analysis.tips && analysis.tips.length > 0 && (() => {
        const categories = [...new Set(analysis.tips.map(t => t.category))];
        const categoryStyles: Record<string, { bg: string; text: string; label: string }> = {
          // AoE2 categories
          economy: { bg: "bg-yellow-500/10", text: "text-yellow-400", label: "Economy" },
          military: { bg: "bg-red-500/10", text: "text-red-400", label: "Military" },
          strategy: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Strategy" },
          // CS2 categories
          aim: { bg: "bg-red-500/10", text: "text-red-400", label: "Aim" },
          utility: { bg: "bg-green-500/10", text: "text-green-400", label: "Utility" },
          positioning: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Positioning" },
          teamwork: { bg: "bg-purple-500/10", text: "text-purple-400", label: "Teamwork" },
        };
        const defaultStyle = { bg: "bg-zinc-500/10", text: "text-zinc-400", label: "Other" };

        return (
          <div className={`grid gap-4 text-center ${categories.length <= 3 ? 'grid-cols-3' : 'grid-cols-4'}`}>
            {categories.map(cat => {
              const style = categoryStyles[cat] || defaultStyle;
              const count = analysis.tips?.filter(t => t.category === cat).length || 0;
              return (
                <div key={cat} className={`rounded-xl ${style.bg} p-4`}>
                  <div className={`text-2xl font-bold ${style.text}`}>{count}</div>
                  <div className="text-sm text-zinc-400">{style.label} Tips</div>
                </div>
              );
            })}
          </div>
        );
      })()}
    </div>
  );
}
