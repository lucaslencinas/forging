"use client";

import { useMemo } from "react";
import type { components } from "@/types/api";

type AoE2Content = components["schemas"]["AoE2Content"];
type CS2Content = components["schemas"]["CS2Content"];
type TimestampedTip = components["schemas"]["TimestampedTip"];

interface AnalysisTimelineV2Props {
  gameType: string;
  data: AoE2Content | CS2Content | null | undefined;
  tips?: TimestampedTip[];
  currentTime: number;
  duration: number;
  onSeek: (seconds: number) => void;
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

function isAoE2Content(
  data: AoE2Content | CS2Content | null | undefined
): data is AoE2Content {
  return data !== null && data !== undefined && "players_timeline" in data;
}

function isCS2Content(
  data: AoE2Content | CS2Content | null | undefined
): data is CS2Content {
  return data !== null && data !== undefined && "rounds_timeline" in data;
}

export function AnalysisTimelineV2({
  gameType,
  data,
  tips,
  currentTime,
  duration,
  onSeek,
}: AnalysisTimelineV2Props) {
  // --- SUB-COMPONENT: AOE2 AGE BARS ---
  const AoE2Timeline = () => {
    if (!isAoE2Content(data)) return null;

    const playersTimeline = data.players_timeline;
    if (!playersTimeline || playersTimeline.length === 0) return null;

    // Use POV player or first player for V2 prototype
    const povPlayer =
      playersTimeline[data.pov_player_index ?? 0] ?? playersTimeline[0];
    if (!povPlayer) return null;

    const maxTime = duration || 1800;

    const events = [
      {
        name: "Dark Age",
        roman: "I",
        start: 0,
        end: povPlayer.feudal_age_seconds,
        color: "from-amber-800 to-amber-900",
        activeColor: "from-amber-600 to-amber-700",
      },
      {
        name: "Feudal Age",
        roman: "II",
        start: povPlayer.feudal_age_seconds,
        end: povPlayer.castle_age_seconds,
        color: "from-amber-700 to-amber-900",
        activeColor: "from-amber-500 to-amber-600",
      },
      {
        name: "Castle Age",
        roman: "III",
        start: povPlayer.castle_age_seconds,
        end: povPlayer.imperial_age_seconds,
        color: "from-green-700 to-green-900",
        activeColor: "from-green-500 to-green-600",
      },
      {
        name: "Imperial Age",
        roman: "IV",
        start: povPlayer.imperial_age_seconds,
        end: maxTime,
        color: "from-purple-700 to-purple-900",
        activeColor: "from-purple-500 to-purple-600",
      },
    ].filter(
      (
        e
      ): e is {
        name: string;
        roman: string;
        start: number;
        end: number | null | undefined;
        color: string;
        activeColor: string;
      } => e.start !== undefined && e.start !== null
    );

    return (
      <div className="flex-1 flex gap-1 h-full items-center px-2">
        {events.map((evt) => {
          const end = evt.end ?? maxTime;
          const width = Math.max(0, ((end - evt.start) / maxTime) * 100);
          const isActive = currentTime >= evt.start && currentTime < end;

          return (
            <div
              key={evt.name}
              onClick={() => onSeek(evt.start)}
              className={`
                relative h-8 rounded-md bg-gradient-to-r cursor-pointer group transition-all duration-300
                ${isActive ? evt.activeColor : evt.color}
                ${isActive ? "ring-2 ring-white/30 shadow-lg" : "opacity-60 hover:opacity-90"}
              `}
              style={{ width: `${width}%`, minWidth: width > 0 ? "40px" : "0" }}
            >
              {/* Roman numeral */}
              {width > 5 && (
                <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white/80">
                  {evt.roman}
                </span>
              )}
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap bg-black/90 text-xs px-3 py-1.5 rounded-lg border border-white/10 z-20">
                <span className="font-bold text-white">{evt.name}</span>
                <span className="ml-2 font-mono text-zinc-400">
                  {formatTime(evt.start)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // --- SUB-COMPONENT: CS2 ROUNDS ---
  const CS2Timeline = () => {
    if (!isCS2Content(data)) return null;

    const rounds = data.rounds_timeline;

    // Count tips per round
    const tipsPerRound = useMemo(() => {
      if (!tips || tips.length === 0) return {};
      const counts: Record<number, number> = {};
      for (const round of rounds) {
        counts[round.round] = tips.filter(
          (t) =>
            t.timestamp_seconds >= round.start_seconds &&
            t.timestamp_seconds <= round.end_seconds
        ).length;
      }
      return counts;
    }, [rounds, tips]);

    return (
      <div className="flex-1 flex items-center h-full overflow-x-auto custom-scrollbar gap-1.5 px-4">
        {rounds.map((round) => {
          const isActive =
            currentTime >= round.start_seconds &&
            currentTime <= round.end_seconds;
          const isDead = round.death_seconds != null;
          const tipCount = tipsPerRound[round.round] || 0;

          return (
            <button
              key={round.round}
              onClick={() => onSeek(round.start_seconds)}
              className={`
                relative shrink-0 h-10 min-w-[44px] px-2 rounded-lg text-xs font-bold tracking-tight flex flex-col items-center justify-center border transition-all
                ${
                  isActive
                    ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white border-amber-400 shadow-lg shadow-amber-500/30 scale-105"
                    : isDead
                      ? "bg-red-900/30 text-red-400 border-red-900/50 hover:bg-red-900/50 hover:border-red-500/50"
                      : "bg-white/5 text-zinc-400 border-white/10 hover:bg-white/10 hover:text-white hover:border-white/20"
                }
              `}
              title={`Round ${round.round}: ${round.start_time} - ${round.end_time}${isDead ? ` (Died at ${round.death_time})` : ""}`}
            >
              <span className="leading-none">R{round.round}</span>
              {/* Death indicator */}
              {isDead && (
                <span className="text-[8px] text-red-400 leading-none mt-0.5">
                  X
                </span>
              )}
              {/* Tips count badge */}
              {tipCount > 0 && !isActive && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] font-bold flex items-center justify-center">
                  {tipCount}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  };

  return (
    <div className="h-full w-full flex items-center px-6 gap-4 relative">
      {/* Playhead Time */}
      <div className="flex flex-col font-mono text-xs leading-none text-right w-16 shrink-0">
        <span className="text-amber-400 font-semibold">
          {formatTime(currentTime)}
        </span>
        <span className="text-zinc-600 mt-0.5">{formatTime(duration || 0)}</span>
      </div>

      {/* Separator */}
      <div className="h-8 w-px bg-white/10" />

      {/* Main Track Logic */}
      <div className="flex-1 h-12 w-full relative flex items-center bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden">
        {gameType === "aoe2" && <AoE2Timeline />}
        {gameType === "cs2" && <CS2Timeline />}
      </div>
    </div>
  );
}
