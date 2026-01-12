"use client";

import { useMemo } from "react";

interface TimestampedTip {
  timestamp_seconds: number;
  timestamp_display: string;
  tip: string;
  category: string;
}

interface TimestampedTipsProps {
  tips: TimestampedTip[];
  currentTime: number;
  onSeek: (seconds: number) => void;
}

const categoryConfig: Record<string, { icon: string; color: string; bgColor: string }> = {
  // AoE2 categories
  economy: {
    icon: "💰",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10 border-yellow-500/30",
  },
  military: {
    icon: "⚔️",
    color: "text-red-400",
    bgColor: "bg-red-500/10 border-red-500/30",
  },
  strategy: {
    icon: "🎯",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10 border-blue-500/30",
  },
  // CS2 categories
  aim: {
    icon: "🎯",
    color: "text-red-400",
    bgColor: "bg-red-500/10 border-red-500/30",
  },
  utility: {
    icon: "💨",
    color: "text-green-400",
    bgColor: "bg-green-500/10 border-green-500/30",
  },
  positioning: {
    icon: "📍",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10 border-blue-500/30",
  },
  teamwork: {
    icon: "🤝",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10 border-purple-500/30",
  },
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function TimestampedTips({ tips, currentTime, onSeek }: TimestampedTipsProps) {
  // Find the current active tip based on video time
  const activeTipIndex = useMemo(() => {
    if (tips.length === 0) return -1;

    // Find the last tip that has passed
    for (let i = tips.length - 1; i >= 0; i--) {
      if (currentTime >= tips[i].timestamp_seconds) {
        return i;
      }
    }
    return -1;
  }, [tips, currentTime]);

  if (tips.length === 0) {
    return (
      <div className="rounded-xl bg-zinc-800/50 p-6 text-center">
        <span className="text-zinc-500">No coaching tips available</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-200">
        <span>📋</span>
        Coaching Tips
        <span className="text-sm font-normal text-zinc-500">
          ({tips.length} tips)
        </span>
      </h3>

      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
        {tips.map((tip, index) => {
          const config = categoryConfig[tip.category] || categoryConfig.strategy;
          const isActive = index === activeTipIndex;
          const isPast = index < activeTipIndex;

          return (
            <button
              key={index}
              onClick={() => onSeek(tip.timestamp_seconds)}
              className={`
                w-full text-left rounded-lg border p-4 transition-all
                hover:bg-zinc-700/50 hover:border-zinc-600
                ${isActive
                  ? `${config.bgColor} ring-2 ring-orange-500/50`
                  : isPast
                    ? "border-zinc-700/50 bg-zinc-800/30 opacity-60"
                    : "border-zinc-700 bg-zinc-800/50"
                }
              `}
            >
              <div className="flex items-start gap-3">
                {/* Timestamp badge */}
                <div className={`
                  flex-shrink-0 rounded-md bg-zinc-900 px-2 py-1
                  font-mono text-sm font-medium
                  ${isActive ? "text-orange-400" : "text-zinc-400"}
                `}>
                  {tip.timestamp_display || formatTime(tip.timestamp_seconds)}
                </div>

                {/* Category icon */}
                <span className="flex-shrink-0 text-lg">
                  {config.icon}
                </span>

                {/* Tip content */}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${isActive ? "text-zinc-100" : "text-zinc-300"}`}>
                    {tip.tip}
                  </p>
                  <span className={`mt-1 inline-block text-xs ${config.color}`}>
                    {tip.category}
                  </span>
                </div>

                {/* Play indicator */}
                <div className={`
                  flex-shrink-0 text-orange-500 transition-opacity
                  ${isActive ? "opacity-100" : "opacity-0"}
                `}>
                  ▶
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
