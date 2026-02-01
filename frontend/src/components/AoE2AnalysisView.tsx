"use client";

import { useRef, useState, useMemo } from "react";
import { VideoPlayer, VideoPlayerRef } from "./VideoPlayer";
import { TimestampedTips } from "./TimestampedTips";
import { useVoiceCoaching } from "@/hooks/useVoiceCoaching";
import type { components } from "@/types/api";

type GameSummary = components["schemas"]["GameSummary"];
type TimestampedTip = components["schemas"]["TimestampedTip"];
type AoE2Content = components["schemas"]["AoE2Content"];
type AoE2PlayerTimeline = components["schemas"]["AoE2PlayerTimeline"];

// Age colors matching the reference image
const AGE_COLORS = {
  dark: "bg-amber-900/80",      // Dark Age - tan/brown
  feudal: "bg-orange-600/80",   // Feudal Age - orange
  castle: "bg-green-600/80",    // Castle Age - green
  imperial: "bg-purple-600/80", // Imperial Age - purple
};

// Format seconds to mm:ss
function formatTime(seconds: number | null | undefined): string {
  if (seconds == null) return "--:--";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

interface AoE2AnalysisViewProps {
  tips: TimestampedTip[];
  gameSummary?: GameSummary | null;
  aoe2Content?: AoE2Content | null;
  videoUrl: string;
  audioUrls?: string[];
  modelUsed?: string;
  provider?: string;
  shareUrl?: string;
  error?: string | null;
}

export function AoE2AnalysisView({
  tips,
  gameSummary,
  aoe2Content,
  videoUrl,
  audioUrls = [],
  modelUsed,
  provider,
  shareUrl,
  error,
}: AoE2AnalysisViewProps) {
  const videoRef = useRef<VideoPlayerRef>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [copied, setCopied] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  // Voice coaching hook
  useVoiceCoaching(tips, audioUrls, currentTime, voiceEnabled);

  const handleSeek = (seconds: number) => {
    videoRef.current?.seek(seconds);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleCopyShareUrl = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const hasAudio = audioUrls.length > 0;
  const hasCivilizations = gameSummary?.players?.some((p) => p.civilization);

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

          {/* Age Progression Timeline */}
          {aoe2Content?.players_timeline && aoe2Content.players_timeline.length > 0 && (
            <AgeProgressionTimeline
              players={aoe2Content.players_timeline}
              videoDuration={gameSummary?.duration}
              povPlayerIndex={aoe2Content.pov_player_index}
            />
          )}

          <p className="text-center text-xs text-zinc-500">
            Click on a tip to jump to that moment in the video
          </p>
        </div>

        {/* Tips sidebar */}
        <div className="w-full lg:w-[380px] lg:flex-shrink-0">
          <TimestampedTips
            tips={tips}
            currentTime={currentTime}
            onSeek={handleSeek}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * Minimalist age progression timeline showing when each player advanced ages.
 * Displays colored segments for each age with icons on hover for exact times.
 */
function AgeProgressionTimeline({
  players,
  videoDuration,
  povPlayerIndex,
}: {
  players: AoE2PlayerTimeline[];
  videoDuration?: string;
  povPlayerIndex?: number | null;
}) {
  // Parse duration string (e.g., "25:30" or "1:05:30") to seconds
  const totalSeconds = useMemo(() => {
    if (!videoDuration) return 1800; // Default 30 min
    const parts = videoDuration.split(":").map(Number);
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return 1800;
  }, [videoDuration]);

  // Find the max age-up time across all players for scaling
  const maxTime = useMemo(() => {
    let max = 0;
    for (const p of players) {
      if (p.imperial_age_seconds && p.imperial_age_seconds > max) max = p.imperial_age_seconds;
      else if (p.castle_age_seconds && p.castle_age_seconds > max) max = p.castle_age_seconds;
      else if (p.feudal_age_seconds && p.feudal_age_seconds > max) max = p.feudal_age_seconds;
    }
    // Use the larger of max age-up time or video duration
    return Math.max(max + 60, totalSeconds); // Add buffer after last age-up
  }, [players, totalSeconds]);

  return (
    <div className="mt-2 rounded-lg border border-zinc-700 bg-zinc-800/50 p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-zinc-400">Age Progression (from replay)</span>
        <div className="flex gap-2 text-[10px] text-zinc-500">
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded ${AGE_COLORS.dark}`} /> Dark
          </span>
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded ${AGE_COLORS.feudal}`} /> Feudal
          </span>
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded ${AGE_COLORS.castle}`} /> Castle
          </span>
          <span className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded ${AGE_COLORS.imperial}`} /> Imperial
          </span>
        </div>
      </div>

      <div className="space-y-1">
        {players.map((player, idx) => (
          <PlayerAgeBar
            key={idx}
            player={player}
            maxTime={maxTime}
            isPov={povPlayerIndex === idx}
          />
        ))}
      </div>

      {/* Time markers */}
      <div className="flex justify-between mt-1 text-[10px] text-zinc-600">
        <span>0:00</span>
        <span>{formatTime(Math.floor(maxTime / 2))}</span>
        <span>{formatTime(maxTime)}</span>
      </div>
    </div>
  );
}

function PlayerAgeBar({
  player,
  maxTime,
  isPov,
}: {
  player: AoE2PlayerTimeline;
  maxTime: number;
  isPov?: boolean;
}) {
  const [hoveredAge, setHoveredAge] = useState<string | null>(null);

  // Calculate segment widths as percentages
  const feudalStart = player.feudal_age_seconds ?? maxTime;
  const castleStart = player.castle_age_seconds ?? maxTime;
  const imperialStart = player.imperial_age_seconds ?? maxTime;

  const darkWidth = (feudalStart / maxTime) * 100;
  const feudalWidth = ((castleStart - feudalStart) / maxTime) * 100;
  const castleWidth = ((imperialStart - castleStart) / maxTime) * 100;
  const imperialWidth = ((maxTime - imperialStart) / maxTime) * 100;

  // Only show segments that exist
  const hasFeudal = player.feudal_age_seconds != null;
  const hasCastle = player.castle_age_seconds != null;
  const hasImperial = player.imperial_age_seconds != null;

  return (
    <div className={`group relative ${isPov ? "ring-1 ring-orange-500/50 rounded-lg p-1 -m-1" : ""}`}>
      {/* Player name */}
      <div className="flex items-center gap-2 mb-0.5">
        {isPov && <span className="text-[10px] text-orange-400 font-medium">YOU →</span>}
        <span className={`text-[10px] truncate max-w-[100px] ${isPov ? "text-orange-300 font-medium" : "text-zinc-400"}`} title={player.name}>
          {player.name}
        </span>
        <span className="text-[10px] text-zinc-600">({player.civilization})</span>
        {player.winner && <span className="text-[10px] text-yellow-500">👑</span>}
      </div>

      {/* Age bar */}
      <div className={`flex h-4 rounded overflow-hidden ${isPov ? "ring-1 ring-orange-500/30" : ""}`}>
        {/* Dark Age */}
        <div
          className={`${AGE_COLORS.dark} flex items-center justify-center cursor-pointer transition-opacity hover:opacity-80`}
          style={{ width: `${darkWidth}%` }}
          onMouseEnter={() => setHoveredAge("dark")}
          onMouseLeave={() => setHoveredAge(null)}
          title={`Dark Age: 0:00 - ${formatTime(player.feudal_age_seconds)}`}
        >
          {darkWidth > 8 && <span className="text-[10px] text-white/70">I</span>}
        </div>

        {/* Feudal Age */}
        {hasFeudal && feudalWidth > 0 && (
          <div
            className={`${AGE_COLORS.feudal} flex items-center justify-center cursor-pointer transition-opacity hover:opacity-80`}
            style={{ width: `${feudalWidth}%` }}
            onMouseEnter={() => setHoveredAge("feudal")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Feudal Age: ${formatTime(player.feudal_age_seconds)} - ${formatTime(player.castle_age_seconds)}`}
          >
            {feudalWidth > 8 && <span className="text-[10px] text-white/70">II</span>}
          </div>
        )}

        {/* Castle Age */}
        {hasCastle && castleWidth > 0 && (
          <div
            className={`${AGE_COLORS.castle} flex items-center justify-center cursor-pointer transition-opacity hover:opacity-80`}
            style={{ width: `${castleWidth}%` }}
            onMouseEnter={() => setHoveredAge("castle")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Castle Age: ${formatTime(player.castle_age_seconds)} - ${formatTime(player.imperial_age_seconds)}`}
          >
            {castleWidth > 8 && <span className="text-[10px] text-white/70">III</span>}
          </div>
        )}

        {/* Imperial Age */}
        {hasImperial && imperialWidth > 0 && (
          <div
            className={`${AGE_COLORS.imperial} flex items-center justify-center cursor-pointer transition-opacity hover:opacity-80`}
            style={{ width: `${imperialWidth}%` }}
            onMouseEnter={() => setHoveredAge("imperial")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Imperial Age: ${formatTime(player.imperial_age_seconds)}+`}
          >
            {imperialWidth > 8 && <span className="text-[10px] text-white/70">IV</span>}
          </div>
        )}
      </div>

      {/* Hover tooltip */}
      {hoveredAge && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-200 whitespace-nowrap z-10">
          {hoveredAge === "dark" && `Dark Age: 0:00`}
          {hoveredAge === "feudal" && `Feudal at ${formatTime(player.feudal_age_seconds)}`}
          {hoveredAge === "castle" && `Castle at ${formatTime(player.castle_age_seconds)}`}
          {hoveredAge === "imperial" && `Imperial at ${formatTime(player.imperial_age_seconds)}`}
        </div>
      )}
    </div>
  );
}
