"use client";

import { useRef, useState, useMemo } from "react";
import { VideoPlayer, VideoPlayerRef } from "./VideoPlayer";
import { TimestampedTips } from "./TimestampedTips";
import { useVoiceCoaching } from "@/hooks/useVoiceCoaching";
import type { components } from "@/types/api";

type GameSummary = components["schemas"]["GameSummary"];
type RoundTimeline = components["schemas"]["RoundTimeline"];
type TimestampedTip = components["schemas"]["TimestampedTip"];

interface CS2AnalysisViewProps {
  tips: TimestampedTip[];
  gameSummary?: GameSummary | null;
  roundsTimeline: RoundTimeline[];
  videoUrl: string;
  audioUrls?: string[];
  modelUsed?: string;
  provider?: string;
  shareUrl?: string;
  error?: string | null;
}

export function CS2AnalysisView({
  tips,
  gameSummary,
  roundsTimeline,
  videoUrl,
  audioUrls = [],
  modelUsed,
  provider,
  shareUrl,
  error,
}: CS2AnalysisViewProps) {
  const videoRef = useRef<VideoPlayerRef>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [copied, setCopied] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [focusedRoundIndex, setFocusedRoundIndex] = useState<number | null>(null);

  // Voice coaching hook
  useVoiceCoaching(tips, audioUrls, currentTime, voiceEnabled);

  // Determine which round is currently active based on video time
  const currentRoundIndex = useMemo(() => {
    for (let i = 0; i < roundsTimeline.length; i++) {
      const round = roundsTimeline[i];
      if (currentTime >= round.start_seconds && currentTime <= round.end_seconds) {
        return i;
      }
    }
    return null;
  }, [currentTime, roundsTimeline]);

  // Active round for display - either focused (user clicked) or current (video position)
  const activeRoundIndex = focusedRoundIndex ?? currentRoundIndex;
  const activeRound = activeRoundIndex !== null ? roundsTimeline[activeRoundIndex] : null;

  // Filter tips for the active round only
  const filteredTips = useMemo(() => {
    if (!activeRound) return tips;

    return tips.filter((tip) => {
      const tipTime = tip.timestamp_seconds;
      // Tip is valid for this round if within round bounds
      // AND within alive time (before death if player died)
      const roundStart = activeRound.start_seconds;
      const roundEnd = activeRound.death_seconds ?? activeRound.end_seconds;
      return tipTime >= roundStart && tipTime <= roundEnd;
    });
  }, [tips, activeRound]);

  const handleSeek = (seconds: number) => {
    videoRef.current?.seek(seconds);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleRoundChange = (index: number) => {
    if (index >= 0 && index < roundsTimeline.length) {
      setFocusedRoundIndex(index);
      // Seek video to start of selected round
      videoRef.current?.seek(roundsTimeline[index].start_seconds);
    }
  };

  const handleCopyShareUrl = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const hasAudio = audioUrls.length > 0;

  return (
    <div className="space-y-6">
      {/* Share URL */}
      {shareUrl && (
        <div className="flex items-center gap-3 rounded-xl border border-green-500/30 bg-green-500/10 p-4">
          <div className="flex-1">
            <p className="text-sm font-medium text-green-400">Analysis saved!</p>
            <p className="text-xs text-zinc-400 mt-1">Share this link with others:</p>
            <p className="text-sm text-zinc-300 mt-1 font-mono truncate">{shareUrl}</p>
          </div>
          <button
            onClick={handleCopyShareUrl}
            className="shrink-0 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700"
          >
            {copied ? "Copied!" : "Copy Link"}
          </button>
        </div>
      )}

      {/* Game Summary */}
      {gameSummary && (
        <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-4">
          <h3 className="mb-3 text-sm font-medium text-zinc-400">Game Info</h3>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
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
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400">
          <span className="font-medium">Analysis Error:</span> {error}
        </div>
      )}

      {/* Main content: Video + Tips */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Video Player */}
        <div className="flex-1 min-w-0 space-y-2">
          <VideoPlayer
            ref={videoRef}
            src={videoUrl}
            onTimeUpdate={handleTimeUpdate}
            className="aspect-video"
            voiceEnabled={hasAudio ? voiceEnabled : undefined}
            onVoiceToggle={hasAudio ? () => setVoiceEnabled(!voiceEnabled) : undefined}
          />

          {/* Round Carousel Navigation - below video like AoE2 age progression */}
          {roundsTimeline.length > 0 && (
            <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-zinc-400">Rounds</h3>
                {activeRound && (
                  <div className="text-xs text-zinc-500">
                    Showing tips for Round {activeRound.round}
                    {activeRound.death_time && (
                      <span className="text-red-400 ml-2">
                        (Died at {activeRound.death_time})
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Round buttons */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => activeRoundIndex !== null && handleRoundChange(activeRoundIndex - 1)}
                  disabled={activeRoundIndex === null || activeRoundIndex <= 0}
                  className="p-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  title="Previous round"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>

                <div className="flex-1 overflow-x-auto">
                  <div className="flex gap-1 justify-center">
                    {roundsTimeline.map((round, index) => {
                      const isCurrent = index === currentRoundIndex;
                      const tipCount = tips.filter(
                        (t) => t.timestamp_seconds >= round.start_seconds &&
                               t.timestamp_seconds <= (round.death_seconds ?? round.end_seconds)
                      ).length;

                      return (
                        <button
                          key={round.round}
                          onClick={() => handleRoundChange(index)}
                          className={`
                            min-w-[48px] px-3 py-2 rounded-lg transition-all text-center
                            ${isCurrent
                              ? "bg-blue-500 text-white ring-2 ring-blue-400"
                              : "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
                            }
                          `}
                        >
                          <div className="text-sm font-medium">R{round.round}</div>
                          <div className="text-xs opacity-70">{tipCount} tips</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <button
                  onClick={() => activeRoundIndex !== null && handleRoundChange(activeRoundIndex + 1)}
                  disabled={activeRoundIndex === null || activeRoundIndex >= roundsTimeline.length - 1}
                  className="p-2 rounded-lg bg-zinc-700 hover:bg-zinc-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  title="Next round"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          <p className="text-center text-xs text-zinc-500">
            Click on a tip to jump to that moment in the video
          </p>
        </div>

        {/* Filtered Tips for current round */}
        <div className="w-full lg:w-[380px] lg:flex-shrink-0">
          <TimestampedTips
            tips={filteredTips}
            currentTime={currentTime}
            onSeek={handleSeek}
          />
        </div>
      </div>
    </div>
  );
}
