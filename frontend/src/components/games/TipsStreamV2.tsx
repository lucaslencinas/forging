"use client";

import { useState, useEffect, useRef } from "react";
import type { components } from "@/types/api";

type TimestampedTip = components["schemas"]["TimestampedTip"];

interface TipsStreamV2Props {
  tips: TimestampedTip[];
}

// Auto-collapse after 20 seconds of inactivity
const AUTO_COLLAPSE_MS = 20000;

const categoryConfig: Record<
  string,
  { icon: string; color: string; pillColor: string }
> = {
  // AoE2 categories
  economy: {
    icon: "G",
    color: "text-amber-400",
    pillColor: "bg-amber-500/20 text-amber-400",
  },
  military: {
    icon: "!",
    color: "text-red-500",
    pillColor: "bg-red-500/20 text-red-400",
  },
  strategy: {
    icon: "*",
    color: "text-zinc-300",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  // CS2 categories
  aim: {
    icon: "*",
    color: "text-red-500",
    pillColor: "bg-red-500/20 text-red-400",
  },
  utility: {
    icon: "~",
    color: "text-zinc-300",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  positioning: {
    icon: "@",
    color: "text-zinc-300",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  teamwork: {
    icon: "+",
    color: "text-zinc-300",
    pillColor: "bg-zinc-500/20 text-zinc-300",
  },
  // CS2 Observer categories
  exploitable_pattern: {
    icon: "!",
    color: "text-red-500",
    pillColor: "bg-red-500/20 text-red-400",
  },
  rank_up_habit: {
    icon: "^",
    color: "text-amber-400",
    pillColor: "bg-amber-500/20 text-amber-400",
  },
  missed_adaptation: {
    icon: "?",
    color: "text-yellow-400",
    pillColor: "bg-yellow-500/20 text-yellow-400",
  },
};

export function TipsStreamV2({ tips }: TipsStreamV2Props) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const autoCollapseTimer = useRef<NodeJS.Timeout | null>(null);

  // Auto-collapse after 20 seconds when tips are visible
  useEffect(() => {
    if (!isCollapsed && tips && tips.length > 0) {
      // Clear any existing timer
      if (autoCollapseTimer.current) {
        clearTimeout(autoCollapseTimer.current);
      }
      // Set new timer to auto-collapse
      autoCollapseTimer.current = setTimeout(() => {
        setIsCollapsed(true);
      }, AUTO_COLLAPSE_MS);

      return () => {
        if (autoCollapseTimer.current) {
          clearTimeout(autoCollapseTimer.current);
        }
      };
    }
  }, [isCollapsed, tips]);

  // Reset collapsed state when new tips appear
  useEffect(() => {
    if (tips && tips.length > 0) {
      setIsCollapsed(false);
    }
  }, [tips?.map(t => t.timestamp_seconds).join(',')]);

  // If no tips, don't render anything
  if (!tips || tips.length === 0) {
    return null;
  }

  // Collapsed state - show hamburger menu button
  if (isCollapsed) {
    return (
      <button
        onClick={() => setIsCollapsed(false)}
        className="w-10 h-10 rounded-lg bg-black/60 backdrop-blur-xl border border-white/10 flex items-center justify-center hover:bg-black/80 transition-colors"
        title="Show tips"
      >
        <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
    );
  }

  // Show floating tips as HUD notifications
  // Tip text is NEVER cropped - collapsed shows full tip, expand shows reasoning
  return (
    <div className="flex flex-col gap-3 w-80 items-end">
      {/* Close button */}
      <button
        onClick={() => setIsCollapsed(true)}
        className="self-end w-8 h-8 rounded-lg bg-black/60 backdrop-blur-xl border border-white/10 flex items-center justify-center hover:bg-black/80 transition-colors -mb-1"
        title="Collapse tips"
      >
        <svg className="w-4 h-4 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {tips?.slice(0, 3).map((tip, idx) => {
        const config = categoryConfig[tip.category] || categoryConfig.strategy;
        const isExpanded = expandedIndex === idx;
        const hasDetails = tip.reasoning || tip.confidence;

        return (
          <div
            key={idx}
            onClick={() => hasDetails && setExpandedIndex(isExpanded ? null : idx)}
            className={`
              bg-black/60 backdrop-blur-xl border border-white/10 p-4 rounded-xl text-sm text-white/90
              shadow-2xl animate-in slide-in-from-right-8 fade-in duration-500
              ${hasDetails ? "cursor-pointer hover:border-amber-500/30 transition-all" : ""}
            `}
            style={{ animationDelay: `${idx * 200}ms` }}
          >
            <div className="flex justify-between items-center mb-2">
              <div className="flex items-center gap-2">
                <span className="text-amber-400 font-mono text-xs">
                  {tip.timestamp_display}
                </span>
                <span
                  className={`text-[10px] uppercase tracking-wider border border-white/10 px-1.5 py-0.5 rounded ${config.pillColor}`}
                >
                  {tip.category}
                </span>
              </div>
              {tip.confidence && tip.confidence >= 8 && (
                <span className="text-[10px] text-green-500 font-mono">
                  {tip.confidence}/10
                </span>
              )}
            </div>

            {/* Tip text - NEVER cropped */}
            <p className="leading-relaxed font-light">{tip.tip}</p>

            {/* Expanded content: reasoning and confidence details */}
            {isExpanded && hasDetails && (
              <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
                {/* Confidence indicator */}
                {tip.confidence && (
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-zinc-500 font-medium">
                      Confidence:
                    </span>
                    <div className="h-1.5 flex-1 max-w-[100px] bg-zinc-800/50 rounded-full overflow-hidden border border-white/10">
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
                    <span className="text-xs font-semibold text-zinc-400">
                      {tip.confidence}/10
                    </span>
                  </div>
                )}

                {/* Reasoning */}
                {tip.reasoning && (
                  <div className="text-xs text-zinc-400 leading-relaxed bg-white/5 rounded-lg p-2 border border-white/5">
                    <span className="text-zinc-500 font-medium">Why: </span>
                    {tip.reasoning}
                  </div>
                )}
              </div>
            )}

            {/* Expand hint */}
            {hasDetails && (
              <div className="mt-2 text-[10px] text-zinc-600">
                {isExpanded ? "Click to collapse" : "Click to expand details"}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
