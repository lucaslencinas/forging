"use client";

import { motion } from "motion/react";

interface BulletListProps {
  items: string[];
  variant?: "default" | "amber" | "green" | "muted";
  className?: string;
  staggerDelay?: number;
}

const variantStyles = {
  default: {
    bullet: "bg-amber-500",
    text: "text-white",
  },
  amber: {
    bullet: "bg-amber-500",
    text: "text-amber-100",
  },
  green: {
    bullet: "bg-green-500",
    text: "text-green-100",
  },
  muted: {
    bullet: "bg-zinc-600",
    text: "text-zinc-300",
  },
};

export function BulletList({
  items,
  variant = "default",
  className = "",
  staggerDelay = 0.1,
}: BulletListProps) {
  const styles = variantStyles[variant];

  return (
    <ul className={`space-y-4 ${className}`}>
      {items.map((item, index) => (
        <motion.li
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * staggerDelay, duration: 0.3 }}
          className="flex items-start gap-3"
        >
          <span
            className={`w-2 h-2 rounded-full ${styles.bullet} mt-2.5 flex-shrink-0`}
          />
          <span className={`text-xl md:text-2xl ${styles.text}`}>{item}</span>
        </motion.li>
      ))}
    </ul>
  );
}
