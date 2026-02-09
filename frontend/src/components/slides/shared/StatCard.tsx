"use client";

import { motion } from "motion/react";

interface StatCardProps {
  value: string;
  label: string;
  delay?: number;
  variant?: "default" | "glow" | "gradient";
}

export function StatCard({
  value,
  label,
  delay = 0,
  variant = "default",
}: StatCardProps) {
  const baseClasses =
    "flex flex-col items-center justify-center p-6 md:p-8 rounded-2xl";

  const variantClasses = {
    default: "bg-zinc-900 border border-zinc-800",
    glow: "bg-zinc-900/80 border border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.15)]",
    gradient:
      "bg-gradient-to-br from-zinc-900 to-zinc-800 border border-zinc-700",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.4, ease: "easeOut" }}
      className={`${baseClasses} ${variantClasses[variant]}`}
    >
      <motion.span
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: delay + 0.2, duration: 0.3 }}
        className="text-4xl md:text-6xl font-bold text-amber-500 font-mono"
      >
        {value}
      </motion.span>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.4, duration: 0.3 }}
        className="text-lg md:text-xl text-zinc-400 mt-2"
      >
        {label}
      </motion.span>
    </motion.div>
  );
}
