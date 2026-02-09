"use client";

import { motion } from "motion/react";

interface SlideProgressProps {
  current: number;
  total: number;
  variant?: "default" | "minimal" | "glow";
}

export function SlideProgress({
  current,
  total,
  variant = "default",
}: SlideProgressProps) {
  const progress = (current / total) * 100;

  const barStyles = {
    default: "bg-amber-500",
    minimal: "bg-white/50",
    glow: "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]",
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      {/* Progress bar */}
      <div className="h-1 bg-zinc-800">
        <motion.div
          className={`h-full ${barStyles[variant]}`}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />
      </div>

      {/* Slide counter */}
      <div className="absolute bottom-4 right-4 text-zinc-500 font-mono text-sm">
        {current} / {total}
      </div>
    </div>
  );
}
