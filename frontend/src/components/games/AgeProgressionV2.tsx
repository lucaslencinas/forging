"use client";

import { useState, useMemo } from "react";
import type { components } from "@/types/api";

type AoE2PlayerTimeline = components["schemas"]["AoE2PlayerTimeline"];

interface AgeProgressionV2Props {
  players: AoE2PlayerTimeline[];
  videoDuration?: string;
  povPlayerIndex?: number | null;
}

// Format seconds to mm:ss
function formatTime(seconds: number | null | undefined): string {
  if (seconds == null) return "--:--";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Age progression component showing when each player advanced ages.
 * Displays colored segments for each age with Roman numerals and timestamps.
 * This component appears below the video, separate from the bottom timeline.
 */
export function AgeProgressionV2({
  players,
  videoDuration,
  povPlayerIndex,
}: AgeProgressionV2Props) {
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
      if (p.imperial_age_seconds && p.imperial_age_seconds > max)
        max = p.imperial_age_seconds;
      else if (p.castle_age_seconds && p.castle_age_seconds > max)
        max = p.castle_age_seconds;
      else if (p.feudal_age_seconds && p.feudal_age_seconds > max)
        max = p.feudal_age_seconds;
    }
    // Use the larger of max age-up time or video duration
    return Math.max(max + 60, totalSeconds); // Add buffer after last age-up
  }, [players, totalSeconds]);

  if (!players || players.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-white font-semibold">Age Progression</span>
        <span className="text-xs text-zinc-500">(in-game time)</span>
      </div>

      <div className="space-y-2.5">
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
      <div className="flex justify-between mt-3 text-xs text-zinc-600 font-mono">
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
    <div
      className={`group relative ${isPov ? "bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/30 rounded-lg p-2" : "p-1"}`}
    >
      {/* Player name */}
      <div className="flex items-center gap-2 mb-1.5">
        {isPov && (
          <span className="text-xs text-amber-400 font-semibold">YOU</span>
        )}
        <span
          className={`text-xs truncate max-w-[120px] ${isPov ? "text-amber-300 font-semibold" : "text-zinc-300"}`}
          title={player.name}
        >
          {player.name}
        </span>
        <span className="text-xs text-zinc-600">({player.civilization})</span>
        {player.winner && (
          <svg className="w-3.5 h-3.5 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
          </svg>
        )}
      </div>

      {/* Age bar */}
      <div
        className={`flex h-5 rounded-lg overflow-hidden border transition-all ${isPov ? "border-amber-500/50 ring-1 ring-amber-500/20" : "border-white/10"}`}
      >
        {/* Dark Age - amber/yellow muted */}
        <div
          className="relative bg-gradient-to-br from-amber-700 to-amber-900 flex items-center justify-center"
          style={{ width: `${darkWidth}%` }}
          onMouseEnter={() => setHoveredAge("dark")}
          onMouseLeave={() => setHoveredAge(null)}
          title={`Dark Age: 0:00 - ${formatTime(player.feudal_age_seconds)}`}
        >
          {darkWidth > 12 && (
            <span className="text-[10px] text-white/80 font-medium tracking-wide">Dark</span>
          )}
        </div>

        {/* Feudal Age - dark red */}
        {hasFeudal && feudalWidth > 0 && (
          <div
            className="relative bg-gradient-to-br from-red-700 to-red-900 flex items-center justify-center"
            style={{ width: `${feudalWidth}%` }}
            onMouseEnter={() => setHoveredAge("feudal")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Feudal Age: ${formatTime(player.feudal_age_seconds)} - ${formatTime(player.castle_age_seconds)}`}
          >
            {feudalWidth > 12 && (
              <span className="text-[10px] text-white/80 font-medium tracking-wide">Feudal</span>
            )}
          </div>
        )}

        {/* Castle Age - dark blue/purple */}
        {hasCastle && castleWidth > 0 && (
          <div
            className="relative bg-gradient-to-br from-indigo-700 to-indigo-900 flex items-center justify-center"
            style={{ width: `${castleWidth}%` }}
            onMouseEnter={() => setHoveredAge("castle")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Castle Age: ${formatTime(player.castle_age_seconds)} - ${formatTime(player.imperial_age_seconds)}`}
          >
            {castleWidth > 12 && (
              <span className="text-[10px] text-white/80 font-medium tracking-wide">Castle</span>
            )}
          </div>
        )}

        {/* Imperial Age - dark green */}
        {hasImperial && imperialWidth > 0 && (
          <div
            className="relative bg-gradient-to-br from-emerald-700 to-emerald-900 flex items-center justify-center"
            style={{ width: `${imperialWidth}%` }}
            onMouseEnter={() => setHoveredAge("imperial")}
            onMouseLeave={() => setHoveredAge(null)}
            title={`Imperial Age: ${formatTime(player.imperial_age_seconds)}+`}
          >
            {imperialWidth > 12 && (
              <span className="text-[10px] text-white/80 font-medium tracking-wide">Imperial</span>
            )}
          </div>
        )}
      </div>

      {/* Hover tooltip */}
      {hoveredAge && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-900/95 backdrop-blur-sm border border-white/20 rounded-lg px-3 py-1.5 text-xs text-white whitespace-nowrap z-10 shadow-lg">
          {hoveredAge === "dark" && `Dark Age: 0:00`}
          {hoveredAge === "feudal" &&
            `Feudal at ${formatTime(player.feudal_age_seconds)}`}
          {hoveredAge === "castle" &&
            `Castle at ${formatTime(player.castle_age_seconds)}`}
          {hoveredAge === "imperial" &&
            `Imperial at ${formatTime(player.imperial_age_seconds)}`}
        </div>
      )}
    </div>
  );
}
