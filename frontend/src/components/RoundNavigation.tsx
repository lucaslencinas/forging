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
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-white">Rounds:</span>
        <div className="flex flex-wrap gap-2">
          {rounds.map((round) => {
            const isActive = currentRound === round.round;
            const isDead = round.death_seconds !== null && round.death_seconds !== undefined;

            return (
              <button
                key={round.round}
                onClick={() => onSeek(round.start_seconds)}
                className={`
                  min-w-[40px] px-3 py-2 text-sm font-semibold rounded-xl transition-all duration-300
                  border backdrop-blur-sm
                  ${
                    isActive
                      ? "bg-amber-500/20 text-amber-400 border-amber-500 shadow-lg shadow-amber-500/30 ring-2 ring-amber-500/20"
                      : isDead
                      ? "bg-red-900/20 text-red-400 border-red-500/30 hover:bg-red-900/30 hover:border-red-500/50"
                      : "bg-white/5 text-zinc-300 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
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
        <div className="text-sm text-zinc-400 bg-white/5 border border-white/10 rounded-lg p-3 backdrop-blur-sm">
          {(() => {
            const round = rounds.find((r) => r.round === currentRound);
            if (!round) return null;

            return (
              <span>
                <span className="font-semibold text-white">Round {round.round}</span> 
                <span className="text-zinc-600 mx-2">•</span>
                <span className="text-zinc-500">{round.start_time} - {round.end_time}</span>
                {round.death_time && (
                  <>
                    <span className="text-zinc-600 mx-2">•</span>
<span className="text-red-400 font-medium">
                      💀 Died at {round.death_time}
                    </span>
                  </>
                )}
              </span>
            );
          })()}
        </div>
      )}
    </div>
  );
}
