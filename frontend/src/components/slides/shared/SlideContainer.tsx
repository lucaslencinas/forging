"use client";

import { motion } from "motion/react";
import { ReactNode } from "react";

interface SlideContainerProps {
  children: ReactNode;
  className?: string;
}

export function SlideContainer({ children, className = "" }: SlideContainerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`w-full h-full flex flex-col items-center justify-center p-8 md:p-16 ${className}`}
    >
      {children}
    </motion.div>
  );
}
