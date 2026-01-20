"use client";

import { useRef, useState } from "react";
import { VideoPlayer, VideoPlayerRef } from "./VideoPlayer";
import { TimestampedTips } from "./TimestampedTips";
import { useVoiceCoaching } from "@/hooks/useVoiceCoaching";
import type { components } from "@/types/api";

type VideoAnalysisResponse = components["schemas"]["VideoAnalysisResponse"];
type GameSummary = components["schemas"]["GameSummary"];

// Define analysis type that can come from different sources
interface AnalysisData {
  tips?: components["schemas"]["TimestampedTip"][];
  game_summary?: GameSummary | null;
  model_used?: string;
  provider?: string;
  share_url?: string;
  error?: string | null;
}

interface VideoAnalysisResultsProps {
  analysis: AnalysisData;
  videoUrl: string;
  audioUrls?: string[];
}

export function VideoAnalysisResults({ analysis, videoUrl, audioUrls = [] }: VideoAnalysisResultsProps) {
  const videoRef = useRef<VideoPlayerRef>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [copied, setCopied] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true); // Voice ON by default

  // Voice coaching hook - plays tips aloud in sync with video
  const tips = analysis.tips || [];
  useVoiceCoaching(tips, audioUrls, currentTime, voiceEnabled);

  const handleSeek = (seconds: number) => {
    videoRef.current?.seek(seconds);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleCopyShareUrl = async () => {
    if (analysis.share_url) {
      await navigator.clipboard.writeText(analysis.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const gameSummary = analysis.game_summary;
  const hasAudio = audioUrls.length > 0;

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
      {analysis.share_url && (
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
      {gameSummary && (() => {
        const hasCivilizations = gameSummary.players?.some((p) => p.civilization);
        return (
          <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-4">
            <h3 className="mb-3 text-sm font-medium text-zinc-400">Game Info</h3>
            <div className={`grid grid-cols-2 gap-4 ${hasCivilizations ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}>
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
                  {gameSummary.players?.length > 2
                    ? `${gameSummary.players.slice(0, 2).map((p) => p.name).join(" vs ")} +${gameSummary.players.length - 2}`
                    : gameSummary.players?.map((p) => p.name).join(" vs ")}
                </p>
              </div>
              {/* Only show Civilizations for AoE2 (when players have civilization data) */}
              {hasCivilizations && (
                <div>
                  <span className="text-xs text-zinc-500">Civilizations</span>
                  <p className="text-sm text-zinc-200">
                    {gameSummary.players?.map((p) => p.civilization).join(" vs ")}
                  </p>
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* Error message */}
      {analysis.error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <span className="font-medium">Analysis Error:</span> {analysis.error}
        </div>
      )}

      {/* Main content: Video + Tips - side by side layout */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Video Player - takes remaining space */}
        <div className="flex-1 min-w-0 space-y-2">
          <VideoPlayer
            ref={videoRef}
            src={videoUrl}
            onTimeUpdate={handleTimeUpdate}
            className="aspect-video"
            voiceEnabled={hasAudio ? voiceEnabled : undefined}
            onVoiceToggle={hasAudio ? () => setVoiceEnabled(!voiceEnabled) : undefined}
          />
          <p className="text-center text-xs text-zinc-500">
            Click on a tip to jump to that moment in the video
          </p>
        </div>

        {/* Timestamped Tips - fixed width sidebar */}
        <div className="w-full lg:w-[380px] lg:flex-shrink-0">
          <TimestampedTips
            tips={analysis.tips || []}
            currentTime={currentTime}
            onSeek={handleSeek}
          />
        </div>
      </div>

    </div>
  );
}
