"use client";

import { useMemo, useEffect, useRef, useState } from "react";

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

const categoryConfig: Record<string, { icon: string; color: string; bgColor: string; pillColor: string }> = {
  // AoE2 categories
  economy: {
    icon: "💰",
    color: "text-yellow-400",
    bgColor: "bg-yellow-500/10",
    pillColor: "bg-yellow-500/20 text-yellow-400",
  },
  military: {
    icon: "⚔️",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    pillColor: "bg-red-500/20 text-red-400",
  },
  strategy: {
    icon: "🎯",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    pillColor: "bg-blue-500/20 text-blue-400",
  },
  // CS2 categories
  aim: {
    icon: "🎯",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    pillColor: "bg-red-500/20 text-red-400",
  },
  utility: {
    icon: "💨",
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    pillColor: "bg-green-500/20 text-green-400",
  },
  positioning: {
    icon: "📍",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    pillColor: "bg-blue-500/20 text-blue-400",
  },
  teamwork: {
    icon: "🤝",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    pillColor: "bg-purple-500/20 text-purple-400",
  },
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

export function TimestampedTips({ tips, currentTime, onSeek }: TimestampedTipsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeTipRef = useRef<HTMLDivElement>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

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

  // Scroll active tip into view
  useEffect(() => {
    if (activeTipIndex >= 0 && activeTipRef.current && containerRef.current) {
      activeTipRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [activeTipIndex]);

  if (tips.length === 0) {
    return (
      <div className="rounded-xl bg-zinc-800/50 p-6 text-center">
        <span className="text-zinc-500">No coaching tips available</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <h3 className="flex items-center gap-2 text-lg font-semibold text-zinc-200 mb-3">
        <span>📋</span>
        Coaching Tips
        <span className="text-sm font-normal text-zinc-500">
          ({tips.length} tips)
        </span>
      </h3>

      <div
        ref={containerRef}
        className="space-y-2 flex-1 overflow-y-auto pr-1"
        style={{ maxHeight: "calc(100vh - 400px)", minHeight: "300px" }}
      >
        {tips.map((tip, index) => {
          const config = categoryConfig[tip.category] || categoryConfig.strategy;
          const isActive = index === activeTipIndex;
          const isPast = index < activeTipIndex;
          const isExpanded = expandedIndex === index;

          return (
            <div
              key={index}
              ref={isActive ? activeTipRef : undefined}
              className={`
                w-full text-left rounded-lg transition-all
                hover:bg-zinc-700/50
                ${isActive
                  ? "bg-zinc-800 border-l-4 border-orange-500"
                  : isPast
                    ? "bg-zinc-800/30 opacity-60 border-l-4 border-transparent"
                    : "bg-zinc-800/50 border-l-4 border-transparent"
                }
              `}
            >
              <div className="flex items-stretch">
                {/* Timestamp box on left - clicking seeks video */}
                <button
                  onClick={() => onSeek(tip.timestamp_seconds)}
                  className={`
                    w-16 flex-shrink-0 flex flex-col items-center justify-center py-3 rounded-l-lg
                    hover:bg-zinc-800 transition-colors
                    ${isActive ? "bg-zinc-900" : "bg-zinc-900/70"}
                  `}
                  title="Jump to this moment"
                >
                  <span className="text-lg mb-1">{config.icon}</span>
                  <span className={`
                    font-mono text-xs font-medium
                    ${isActive ? "text-orange-400" : "text-zinc-400"}
                  `}>
                    {tip.timestamp_display || formatTime(tip.timestamp_seconds)}
                  </span>
                </button>

                {/* Content on right - clicking expands/collapses */}
                <button
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                  className="flex-1 min-w-0 p-3 flex flex-col justify-between text-left"
                >
                  <p className={`
                    text-sm transition-all
                    ${isExpanded ? "" : "line-clamp-2"}
                    ${isActive ? "text-zinc-100" : "text-zinc-300"}
                  `}>
                    {tip.tip}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className={`
                      inline-block rounded-full px-2 py-0.5 text-xs font-medium
                      ${config.pillColor}
                    `}>
                      {tip.category}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {isExpanded ? "Click to collapse" : "Click to expand"}
                    </span>
                  </div>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
