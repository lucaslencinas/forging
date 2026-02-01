"use client";

import { useMemo } from "react";

interface RoundTimeline {
  round: number;
  start_seconds: number;
  start_time: string;
  end_seconds: number;
  end_time: string;
  death_seconds?: number | null;
  death_time?: string | null;
  status: string;
}

interface RoundNavigationProps {
  rounds: RoundTimeline[];
  currentTime: number;
  onSeek: (seconds: number) => void;
}

export function RoundNavigation({
  rounds,
  currentTime,
  onSeek,
}: RoundNavigationProps) {
  // Find the current round based on currentTime
  const currentRound = useMemo(() => {
    for (const round of rounds) {
      if (
        currentTime >= round.start_seconds &&
        currentTime <= round.end_seconds
      ) {
        return round.round;
      }
    }
    return null;
  }, [currentTime, rounds]);

  if (!rounds || rounds.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-zinc-400">Rounds:</span>
        <div className="flex flex-wrap gap-1">
          {rounds.map((round) => {
            const isActive = currentRound === round.round;
            const isDead = round.death_seconds !== null && round.death_seconds !== undefined;

            return (
              <button
                key={round.round}
                onClick={() => onSeek(round.start_seconds)}
                className={`
                  min-w-[32px] px-2 py-1 text-xs font-medium rounded transition-all
                  ${
                    isActive
                      ? "bg-blue-500 text-white ring-2 ring-blue-400"
                      : isDead
                      ? "bg-red-900/30 text-red-400 hover:bg-red-900/50"
                      : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                  }
                `}
                title={`Round ${round.round}: ${round.start_time} - ${round.end_time} (${round.status})`}
              >
                R{round.round}
              </button>
            );
          })}
        </div>
      </div>

      {/* Current round info */}
      {currentRound !== null && (
        <div className="text-xs text-zinc-500">
          {(() => {
            const round = rounds.find((r) => r.round === currentRound);
            if (!round) return null;

            return (
              <span>
                Round {round.round} ({round.start_time} - {round.end_time})
                {round.death_time && (
                  <span className="text-red-400 ml-2">
                    Died at {round.death_time}
                  </span>
                )}
              </span>
            );
          })()}
        </div>
      )}
    </div>
  );
}
