"use client";

import { useMemo, useEffect, useRef, useState } from "react";

interface TimestampedTip {
  timestamp_seconds: number;
  timestamp_display: string;
  tip: string;
  category: string;
  reasoning?: string | null;
  confidence?: number | null;
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
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    pillColor: "bg-amber-500/20 text-amber-400",
  },
  military: {
    icon: "⚔️",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    pillColor: "bg-red-500/20 text-red-400",
  },
  strategy: {
    icon: "🎯",
    color: "text-zinc-300",
    bgColor: "bg-zinc-500/10",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  // CS2 categories
  aim: {
    icon: "🎯",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    pillColor: "bg-red-500/20 text-red-400",
  },
  utility: {
    icon: "💨",
    color: "text-zinc-300",
    bgColor: "bg-zinc-500/10",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  positioning: {
    icon: "📍",
    color: "text-zinc-300",
    bgColor: "bg-zinc-500/10",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  teamwork: {
    icon: "🤝",
    color: "text-zinc-300",
    bgColor: "bg-zinc-500/10",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  // CS2 Observer categories
  exploitable_pattern: {
    icon: "🔓",
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    pillColor: "bg-red-500/20 text-red-400",
  },
  rank_up_habit: {
    icon: "📈",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    pillColor: "bg-amber-500/20 text-amber-400",
  },
  missed_adaptation: {
    icon: "🔄",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    pillColor: "bg-amber-500/20 text-amber-400",
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
      <h3 className="flex items-center gap-2 text-xl font-semibold text-white mb-4">
        <span>📋</span>
        Coaching Tips
        <span className="text-sm font-normal text-zinc-500">
          ({tips.length} tips)
        </span>
      </h3>

      <div
        ref={containerRef}
        className="space-y-3 flex-1 overflow-y-auto pr-1"
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
                relative rounded-2xl border transition-all duration-300
                backdrop-blur-sm overflow-hidden
                ${isActive
                  ? "bg-white/10 border-amber-500 shadow-lg shadow-amber-500/20"
                  : isPast
                    ? "bg-white/[0.02] border-white/5 opacity-50"
                    : "bg-white/5 border-white/10 hover:bg-white/[0.07] hover:border-white/20"
                }
              `}
            >
              {/* Orange accent line for active tip */}
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-amber-400 to-amber-600" />
              )}

              <div className="flex items-stretch">
                {/* Timestamp box on left - clicking seeks video */}
                <button
                  onClick={() => onSeek(tip.timestamp_seconds)}
                  className={`
                    w-20 flex-shrink-0 flex flex-col items-center justify-center py-4 px-2
                    border-r transition-all duration-300
                    ${isActive 
                      ? "border-amber-500/30 bg-amber-500/10" 
                      : "border-white/10 hover:bg-white/5"
                    }
                  `}
                  title="Jump to this moment"
                >
                  <span className="text-2xl mb-1.5">{config.icon}</span>
                  <span className={`
                    font-mono text-xs font-semibold tracking-tight
                    ${isActive ? "text-amber-400" : "text-zinc-400"}
                  `}>
                    {tip.timestamp_display || formatTime(tip.timestamp_seconds)}
                  </span>
                </button>

                {/* Content on right - clicking expands/collapses */}
                <button
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                  className="flex-1 min-w-0 p-4 flex flex-col justify-between text-left"
                >
                  <p className={`
                    text-sm leading-relaxed transition-all
                    ${isExpanded ? "" : "line-clamp-2"}
                    ${isActive ? "text-white font-medium" : "text-zinc-300"}
                  `}>
                    {tip.tip}
                  </p>

                  {/* Expanded content: reasoning and confidence */}
                  {isExpanded && (tip.reasoning || tip.confidence) && (
                    <div className="mt-4 pt-4 border-t border-white/10 space-y-3">
                      {/* Confidence indicator */}
                      {tip.confidence && (
                        <div className="flex items-center gap-3">
                          <span className="text-xs text-zinc-500 font-medium">Confidence:</span>
                          <div className="h-2 flex-1 max-w-[120px] bg-zinc-800/50 rounded-full overflow-hidden border border-white/10">
                            <div
                              className={`h-full transition-all duration-500 ${
                                tip.confidence >= 9
                                  ? "bg-gradient-to-r from-green-500 to-emerald-400"
                                  : tip.confidence >= 8
                                    ? "bg-gradient-to-r from-green-400 to-green-300"
                                    : tip.confidence >= 6
                                      ? "bg-gradient-to-r from-yellow-500 to-amber-400"
                                      : "bg-gradient-to-r from-red-500 to-rose-400"
                              }`}
                              style={{ width: `${tip.confidence * 10}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-zinc-400">{tip.confidence}/10</span>
                        </div>
                      )}

                      {/* Reasoning */}
                      {tip.reasoning && (
                        <div className="text-xs text-zinc-400 leading-relaxed bg-white/5 rounded-lg p-3 border border-white/5">
                          <span className="text-zinc-500 font-medium">Why: </span>
                          {tip.reasoning}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-3 flex items-center gap-2 flex-wrap">
                    <span className={`
                      inline-block rounded-full px-3 py-1 text-xs font-medium
                      ${config.pillColor}
                      border border-white/10
                    `}>
                      {tip.category}
                    </span>
                    {/* Show confidence badge inline when collapsed */}
                    {!isExpanded && tip.confidence && (
                      <span className={`
                        inline-block rounded-full px-2.5 py-1 text-xs font-semibold
                        border border-white/10
                        ${tip.confidence >= 8 ? "bg-green-500/20 text-green-500" : "bg-zinc-500/20 text-zinc-400"}
                      `}>
                        {tip.confidence}/10
                      </span>
                    )}
                    <span className="text-xs text-zinc-600 ml-auto">
                      {isExpanded ? "Click to collapse ↑" : "Click to expand ↓"}
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
