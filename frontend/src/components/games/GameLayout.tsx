"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { Background } from "@/components/layout/Background";

interface GameLayoutProps {
  children: ReactNode;
  gameType: string;
}

export function GameLayout({ children }: GameLayoutProps) {
  return (
    <div className="min-h-screen w-screen bg-zinc-950 text-white font-sans selection:bg-amber-500/30">

      {/* Shared Background */}
      <Background />

      {/* Header - matching layout with home/new pages */}
      <header className="fixed top-0 left-0 right-0 z-50 px-6 py-4 border-b border-zinc-800/50 bg-zinc-950/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <span className="text-2xl font-bold tracking-tighter text-amber-500">FORGING</span>
            <span className="hidden sm:block text-xs text-zinc-500 border-l border-zinc-700 pl-3">
              AI-Powered Game Coaching
            </span>
          </Link>

          {/* Right side of header - intentionally empty for games page */}
          <div className="flex items-center gap-2" />
        </div>
      </header>

      {/* Main Content - scrollable, with padding for fixed header */}
      <main className="relative z-10 pt-16">
        {children}
      </main>

    </div>
  );
}
