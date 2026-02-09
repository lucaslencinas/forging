"use client";

import { useState, useMemo } from "react";
import type { components } from "@/types/api";

type RoundTimeline = components["schemas"]["RoundTimeline"];

interface RoundsProgressionV2Props {
  rounds: RoundTimeline[];
  currentTime: number;
  onSeek?: (seconds: number) => void;
}

/**
 * Rounds progression component showing CS2 rounds as a timeline bar.
 * Displays colored segments for each round with win/loss status and death indicators.
 */
export function RoundsProgressionV2({
  rounds,
  currentTime,
  onSeek,
}: RoundsProgressionV2Props) {
  if (!rounds || rounds.length === 0) {
    return null;
  }

  // Calculate total duration as sum of all round durations
  // This ensures segments fill 100% of the bar width
  const totalDuration = useMemo(() => {
    return rounds.reduce((sum, r) => sum + (r.end_seconds - r.start_seconds), 0);
  }, [rounds]);

  // Count wins and losses based on status field (unknown rounds are not counted)
  const stats = useMemo(() => {
    const wins = rounds.filter((r) => r.status === "win").length;
    const losses = rounds.filter((r) => r.status === "loss").length;
    const unknown = rounds.filter((r) => r.status === "unknown").length;
    const deaths = rounds.filter((r) => r.death_seconds != null).length;
    return { wins, losses, unknown, deaths };
  }, [rounds]);

  // Determine if we need compact mode (small screens or many rounds)
  const isCompact = rounds.length > 8;

  return (
    <div className="mt-2 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm p-3">
      {/* Header - more compact */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-white font-semibold">Rounds</span>
        </div>
        {/* Hide legend on very small screens */}
        <div className="hidden sm:flex gap-2 text-[10px] text-zinc-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-green-600" />
            Win
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm bg-red-600/70" />
            Loss
          </span>
          {stats.unknown > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-zinc-600" />
              Unknown
            </span>
          )}
          {stats.deaths > 0 && (
            <span className="flex items-center gap-1">
              <span className="text-zinc-400">💀</span>
              Death
            </span>
          )}
        </div>
      </div>

      {/* Rounds timeline bar */}
      <div className="flex h-5 rounded-md overflow-hidden border border-white/10 relative">
        {rounds.map((round) => (
          <RoundSegment
            key={round.round}
            round={round}
            totalDuration={totalDuration}
            currentTime={currentTime}
            onSeek={onSeek}
            isCompact={isCompact}
          />
        ))}
      </div>

      {/* Time markers - simplified */}
      <div className="flex justify-between mt-1.5 text-[10px] text-zinc-600 font-mono">
        <span>R1</span>
        {!isCompact && <span>R{Math.ceil(rounds.length / 2)}</span>}
        <span>R{rounds.length}</span>
      </div>
    </div>
  );
}

function RoundSegment({
  round,
  totalDuration,
  currentTime,
  onSeek,
  isCompact,
}: {
  round: RoundTimeline;
  totalDuration: number;
  currentTime: number;
  onSeek?: (seconds: number) => void;
  isCompact?: boolean;
}) {
  const [isHovered, setIsHovered] = useState(false);

  const width = ((round.end_seconds - round.start_seconds) / totalDuration) * 100;
  const isActive = currentTime >= round.start_seconds && currentTime <= round.end_seconds;
  const isWin = round.status === "win";
  const isUnknown = round.status === "unknown";
  const isDeath = round.death_seconds != null;

  // Calculate death position within round
  const deathPosition = isDeath
    ? ((round.death_seconds! - round.start_seconds) / (round.end_seconds - round.start_seconds)) * 100
    : 0;

  const handleClick = () => {
    if (onSeek) {
      onSeek(round.start_seconds);
    }
  };

  return (
    <div
      className={`
        relative flex items-center justify-center transition-all group
        ${isWin
          ? "bg-gradient-to-b from-green-600/70 to-green-700/80"
          : isUnknown
            ? "bg-gradient-to-b from-zinc-500/50 to-zinc-600/60"
            : "bg-gradient-to-b from-red-700/50 to-red-800/60"
        }
        ${isActive ? "ring-1 ring-white/60 z-10 brightness-125" : ""}
        ${onSeek ? "cursor-pointer hover:brightness-110" : ""}
      `}
      style={{ width: `${width}%`, minWidth: "2px" }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      {/* Round number - only show if wide enough and not compact */}
      {width > 5 && !isCompact && (
        <span className="text-[9px] text-white/70 font-medium">{round.round}</span>
      )}

      {/* Death marker - skull icon at bottom */}
      {isDeath && (
        <div
          className="absolute bottom-0 translate-y-0"
          style={{ left: `${Math.min(Math.max(deathPosition, 10), 90)}%`, transform: 'translateX(-50%)' }}
        >
          <div className="text-[8px] opacity-70 group-hover:opacity-100 transition-opacity" title={`Died at ${round.death_time}`}>
            💀
          </div>
        </div>
      )}

      {/* Hover tooltip */}
      {isHovered && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-zinc-900/95 backdrop-blur-sm border border-white/20 rounded px-2 py-1 text-[10px] text-white whitespace-nowrap z-20 shadow-lg">
          <span className="font-semibold">R{round.round}</span>
          <span className={`ml-1.5 ${isWin ? "text-green-400" : isUnknown ? "text-zinc-400" : "text-red-400"}`}>
            {isWin ? "Win" : isUnknown ? "Unknown" : "Loss"}
          </span>
          {isDeath && <span className="ml-1.5 text-zinc-400">💀 {round.death_time}</span>}
        </div>
      )}
    </div>
  );
}
