"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "motion/react";
import Image from "next/image";
import { Slide, SlideContent } from "../slides-data";

interface NeonForgeSlidesProps {
  slide: Slide;
}

// Consistent FORGING branding component
function ForgingBrand({ size = "lg" }: { size?: "sm" | "md" | "lg" | "xl" }) {
  const sizeClasses = {
    sm: "text-2xl",
    md: "text-4xl",
    lg: "text-6xl md:text-8xl",
    xl: "text-7xl md:text-9xl",
  };

  return (
    <span
      className={`${sizeClasses[size]} font-mono font-bold tracking-tighter text-amber-500`}
    >
      FORGING
    </span>
  );
}

export function NeonForgeSlides({ slide }: NeonForgeSlidesProps) {
  return (
    <div className="relative w-full h-full overflow-hidden">
      {/* Grid background */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(245, 158, 11, 0.5) 1px, transparent 1px),
            linear-gradient(90deg, rgba(245, 158, 11, 0.5) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      />

      {/* Scan line effect */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
        }}
      />

      {/* Content */}
      <motion.div
        key={slide.id}
        initial={{ opacity: 0, filter: "blur(10px)" }}
        animate={{ opacity: 1, filter: "blur(0px)" }}
        exit={{ opacity: 0, filter: "blur(10px)" }}
        transition={{ duration: 0.4 }}
        className="relative z-10 w-full h-full flex flex-col items-center justify-center p-8 md:p-16"
      >
        <SlideRenderer slide={slide} />
      </motion.div>
    </div>
  );
}

function SlideRenderer({ slide }: { slide: Slide }) {
  const content = slide.content;

  switch (content.type) {
    case "hook-industry":
      return <HookIndustrySlide content={content} />;
    case "hook-growth":
      return <HookGrowthSlide content={content} />;
    case "hook-problem":
      return <HookProblemSlide content={content} />;
    case "hook-coaching-gap":
      return <HookCoachingGapSlide content={content} />;
    case "prize-pools":
      return <PrizePoolsSlide content={content} />;
    case "intro":
      return <IntroSlide content={content} />;
    case "games":
      return <GamesSlide content={content} />;
    case "demo-transition":
      return <DemoTransitionSlide content={content} />;
    case "market":
      return <MarketSlide content={content} />;
    case "competitors":
      return <CompetitorsSlide content={content} />;
    case "architecture":
      return <ArchitectureSlide content={content} />;
    case "architecture-gemini":
      return <ArchitectureGeminiSlide content={content} />;
    case "architecture-gemini-flow":
      return <ArchitectureGeminiFlowSlide content={content} />;
    case "roadmap":
      return <RoadmapSlide content={content} slide={slide} />;
    case "closing":
      return <ClosingSlide content={content} />;
    default:
      return null;
  }
}

type ExtractContent<T extends SlideContent["type"]> = Extract<
  SlideContent,
  { type: T }
>;

// === HOOK SLIDES ===

function HookIndustrySlide({
  content,
}: {
  content: ExtractContent<"hook-industry">;
}) {
  return (
    <div className="max-w-5xl w-full h-full relative pt-16">
      {/* Background image that extends behind content */}
      {content.image && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[120%] h-[65%] overflow-hidden"
        >
          {/* Gradient overlay for bleed effect */}
          <div className="absolute inset-0 z-10 bg-gradient-to-b from-zinc-950 via-zinc-950/50 to-transparent" />
          <div className="absolute inset-0 z-10 bg-gradient-to-r from-zinc-950 via-transparent to-zinc-950" />
          <Image
            src={content.image}
            alt="Esports arena"
            fill
            className="object-cover"
            style={{ objectPosition: "center 75%" }}
          />
        </motion.div>
      )}

      {/* Content on top */}
      <div className="relative z-20">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-7xl font-bold text-white mb-12 text-center font-mono"
          style={{ textShadow: "0 0 40px rgba(245, 158, 11, 0.3)" }}
        >
          {content.headline}
        </motion.h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {content.stats.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 + i * 0.15 }}
              className="flex flex-col items-center p-8 rounded-2xl border border-amber-500/30 bg-zinc-900/90 backdrop-blur-sm"
              style={{ boxShadow: "0 0 30px rgba(245, 158, 11, 0.15)" }}
            >
              <span className="text-5xl md:text-6xl font-bold text-amber-500 font-mono">
                {stat.value}
              </span>
              <span className="text-lg text-zinc-400 mt-2">{stat.label}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {content.imagePlaceholder && !content.image && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-8 p-6 rounded-xl border-2 border-dashed border-zinc-700 bg-zinc-900/40 text-center relative z-20"
        >
          <span className="text-zinc-500 text-sm italic">
            [Image: {content.imagePlaceholder}]
          </span>
        </motion.div>
      )}
    </div>
  );
}

function HookGrowthSlide({
  content,
}: {
  content: ExtractContent<"hook-growth">;
}) {
  const maxValue = Math.max(...content.chartData.map((d) => d.value));

  return (
    <div className="max-w-5xl w-full">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-7xl font-bold text-white mb-4 text-center font-mono"
        style={{ textShadow: "0 0 40px rgba(245, 158, 11, 0.3)" }}
      >
        {content.headline}
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-xl text-zinc-400 mb-12 text-center"
      >
        {content.subheadline}
      </motion.p>

      {/* Simple bar chart */}
      <div className="flex items-end justify-center gap-4 h-64 mb-8">
        {content.chartData.map((data, i) => (
          <motion.div
            key={i}
            initial={{ height: 0 }}
            animate={{ height: `${(data.value / maxValue) * 100}%` }}
            transition={{ delay: 0.3 + i * 0.1, duration: 0.5 }}
            className="relative flex flex-col items-center"
          >
            <div
              className="w-16 md:w-20 rounded-t-lg bg-gradient-to-t from-amber-600 to-amber-400"
              style={{
                height: "100%",
                boxShadow: "0 0 20px rgba(245, 158, 11, 0.3)",
              }}
            />
            <span className="absolute -top-8 text-amber-400 font-bold text-sm">
              ${data.value}B
            </span>
            <span className="mt-2 text-zinc-500 text-sm">{data.year}</span>
          </motion.div>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center text-zinc-600 text-sm"
      >
        Source: {content.source}
      </motion.p>
    </div>
  );
}

function HookProblemSlide({
  content,
}: {
  content: ExtractContent<"hook-problem">;
}) {
  return (
    <div className="max-w-5xl w-full">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-6xl font-bold text-white mb-16 text-center font-mono"
      >
        {content.headline}
      </motion.h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {content.points.map((point, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.2 }}
            className={`p-6 rounded-2xl border ${
              i === 2
                ? "border-amber-500/40 bg-amber-500/10"
                : "border-zinc-700 bg-zinc-900/60"
            }`}
          >
            {point.image ? (
              <div className="relative h-28 w-full rounded-lg overflow-hidden mb-4">
                <Image
                  src={point.image}
                  alt={point.title}
                  fill
                  className="object-cover"
                />
              </div>
            ) : point.imagePlaceholder ? (
              <div className="p-4 rounded-lg border border-dashed border-zinc-700 bg-zinc-800/40 mb-4">
                <span className="text-zinc-500 text-xs italic">
                  [Image: {point.imagePlaceholder}]
                </span>
              </div>
            ) : null}
            <h3
              className={`text-xl font-bold mb-2 ${i === 2 ? "text-amber-400" : "text-white"}`}
            >
              {point.title}
            </h3>
            <p className="text-zinc-400">{point.description}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function HookCoachingGapSlide({
  content,
}: {
  content: ExtractContent<"hook-coaching-gap">;
}) {
  return (
    <div className="max-w-4xl w-full">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-6xl font-bold text-white mb-4 text-center font-mono"
      >
        {content.headline}
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-xl text-zinc-400 mb-12 text-center"
      >
        {content.subheadline}
      </motion.p>

      <div className="space-y-4">
        {content.tiers.map((tier, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + i * 0.15 }}
            className={`flex items-center justify-between p-6 rounded-xl border ${
              i === 0
                ? "border-green-500/30 bg-green-500/5"
                : i === 1
                  ? "border-amber-500/30 bg-amber-500/5"
                  : "border-red-500/30 bg-red-500/5"
            }`}
          >
            <div>
              <span className="text-xl font-bold text-white">{tier.level}</span>
              <p className="text-zinc-500 text-sm">{tier.description}</p>
            </div>
            <span
              className={`text-2xl font-bold font-mono ${
                i === 0
                  ? "text-green-400"
                  : i === 1
                    ? "text-amber-400"
                    : "text-red-400"
              }`}
            >
              {tier.cost}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// === PRIZE POOLS SLIDE ===

function PrizePoolsSlide({
  content,
}: {
  content: ExtractContent<"prize-pools">;
}) {
  // Parse prize values to get max for proportional widths
  const parseValue = (prize: string) => {
    const num = parseFloat(prize.replace(/[$M,]/g, ""));
    return num;
  };
  const maxPrize = Math.max(...content.games.map((g) => parseValue(g.prize)));

  return (
    <div className="max-w-4xl w-full">
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-6xl font-bold text-white mb-4 text-center font-mono"
        style={{ textShadow: "0 0 40px rgba(245, 158, 11, 0.3)" }}
      >
        {content.headline}
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-xl text-zinc-400 mb-10 text-center"
      >
        {content.subheadline}
      </motion.p>

      <div className="space-y-2">
        {content.games.map((game, i) => {
          const prizeValue = parseValue(game.prize);
          const widthPercent = (prizeValue / maxPrize) * 100;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + i * 0.05 }}
              className="flex items-center gap-4"
            >
              <span className="w-8 text-right text-zinc-500 font-mono text-base">
                {game.rank}
              </span>
              <div className="flex-1 relative">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${widthPercent}%` }}
                  transition={{ delay: 0.4 + i * 0.05, duration: 0.5 }}
                  className="h-9 rounded-r-lg bg-gradient-to-r from-amber-600 to-amber-400"
                  style={{ boxShadow: "0 0 15px rgba(245, 158, 11, 0.2)" }}
                />
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-base font-medium text-zinc-900">
                  {game.name}
                </span>
              </div>
              <span className="w-24 text-right text-amber-400 font-bold font-mono text-base">
                {game.prize}
              </span>
            </motion.div>
          );
        })}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center text-zinc-600 text-sm mt-8"
      >
        Source: {content.source}
      </motion.p>
    </div>
  );
}

// === INTRO SLIDE ===

function IntroSlide({ content }: { content: ExtractContent<"intro"> }) {
  return (
    <div className="text-center max-w-4xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="mb-8"
      >
        <ForgingBrand size="lg" />
      </motion.div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-2xl md:text-3xl text-white mb-12"
      >
        {content.tagline}
      </motion.p>
      <div className="flex flex-col md:flex-row gap-4 justify-center mb-8">
        {content.features.map((feature, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + i * 0.15 }}
            className="px-6 py-4 rounded-xl border border-amber-500/30 bg-amber-500/5 text-white text-lg"
            style={{ boxShadow: "0 0 20px rgba(245, 158, 11, 0.1)" }}
          >
            {feature}
          </motion.div>
        ))}
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
        className="text-xl text-amber-400 font-bold"
        style={{ textShadow: "0 0 20px rgba(245, 158, 11, 0.5)" }}
      >
        {content.highlight}
      </motion.p>
    </div>
  );
}

// === GAMES SLIDE ===

function GamesSlide({ content }: { content: ExtractContent<"games"> }) {
  return (
    <div className="max-w-5xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-12 font-mono"
      >
        Supported Games
      </motion.h2>

      {/* Main supported games */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {content.supported.map((game, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 + i * 0.15 }}
            className="relative overflow-hidden rounded-2xl border-2 border-amber-500/50 bg-zinc-900/80"
            style={{ boxShadow: "0 0 40px rgba(245, 158, 11, 0.2)" }}
          >
            <div className="aspect-video bg-zinc-800 relative">
              {!game.image ? (
                <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
                  [Game Image]
                </div>
              ) : (
                <Image
                  src={game.image}
                  alt={game.name}
                  fill
                  className="object-cover object-top"
                />
              )}
            </div>
            <div className="p-4 flex justify-between items-center">
              <span className="text-xl font-bold text-white">{game.name}</span>
              <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-sm font-mono">
                {game.genre}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Coming soon */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        <h3 className="text-xl text-zinc-400 text-center mb-6">Coming Soon</h3>
        <div className="flex flex-wrap justify-center gap-4">
          {content.comingSoon.map((game, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 + i * 0.1 }}
              className="flex items-center gap-3 px-4 py-2 rounded-xl border border-zinc-700 bg-zinc-900/60"
            >
              <div className="w-10 h-10 rounded-lg overflow-hidden bg-zinc-800 relative">
                <Image
                  src={game.image}
                  alt={game.name}
                  fill
                  className="object-cover"
                />
              </div>
              <span className="text-zinc-300">{game.name}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// === DEMO TRANSITION ===

function DemoTransitionSlide({
  content,
}: {
  content: ExtractContent<"demo-transition">;
}) {
  return (
    <div className="text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring" }}
        className="mb-8"
      >
        <span
          className="text-6xl md:text-8xl font-bold text-amber-500 font-mono"
          style={{ textShadow: "0 0 60px rgba(245, 158, 11, 0.5)" }}
        >
          DEMO
        </span>
      </motion.div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-2xl text-zinc-400"
      >
        {content.message}
      </motion.p>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ delay: 0.6, repeat: Infinity, duration: 2 }}
        className="mt-12 text-zinc-600"
      >
        Switch to browser →
      </motion.div>
    </div>
  );
}

// === MARKET SLIDE ===

function MarketSlide({ content }: { content: ExtractContent<"market"> }) {
  const maxValue = Math.max(...content.chartData.map((d) => d.value));

  return (
    <div className="max-w-5xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-8 font-mono"
      >
        {content.headline}
      </motion.h2>

      {/* Stats row */}
      <div className="flex justify-center gap-12 mb-12">
        {content.stats.map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.1 }}
            className="text-center"
          >
            <span className="text-4xl md:text-5xl font-bold text-amber-500 font-mono">
              {stat.value}
            </span>
            <p className="text-zinc-400 text-base mt-2">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Chart */}
      <div className="flex items-end justify-center gap-3 h-48 mb-6">
        {content.chartData.map((data, i) => (
          <motion.div
            key={i}
            initial={{ height: 0 }}
            animate={{ height: `${(data.value / maxValue) * 100}%` }}
            transition={{ delay: 0.4 + i * 0.08, duration: 0.4 }}
            className="relative flex flex-col items-center"
          >
            <div
              className={`w-12 md:w-16 rounded-t-lg ${
                data.projected
                  ? "bg-gradient-to-t from-amber-800/50 to-amber-600/50 border-2 border-dashed border-amber-500/50"
                  : "bg-gradient-to-t from-amber-600 to-amber-400"
              }`}
              style={{
                height: "100%",
                boxShadow: data.projected
                  ? "none"
                  : "0 0 15px rgba(245, 158, 11, 0.3)",
              }}
            />
            <span className="absolute -top-6 text-amber-400 font-bold text-xs">
              ${data.value}B
            </span>
            <span className="mt-2 text-zinc-500 text-xs">{data.year}</span>
          </motion.div>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="text-center text-zinc-600 text-sm"
      >
        Source: {content.source}
      </motion.p>
    </div>
  );
}

// === COMPETITORS SLIDE ===

function CompetitorsSlide({
  content,
}: {
  content: ExtractContent<"competitors">;
}) {
  return (
    <div className="max-w-5xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-12 font-mono"
      >
        {content.headline}
      </motion.h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {content.competitors.map((comp, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.15 }}
            className="p-6 rounded-xl border border-zinc-700 bg-zinc-900/60"
          >
            <h3 className="text-lg font-bold text-white mb-2">{comp.name}</h3>
            <p className="text-amber-400 text-sm mb-3">{comp.games}</p>
            <p className="text-red-400/80 text-sm">{comp.limitation}</p>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.7 }}
        className="p-6 rounded-xl border-2 border-amber-500/50 bg-amber-500/10 text-center"
        style={{ boxShadow: "0 0 30px rgba(245, 158, 11, 0.15)" }}
      >
        <ForgingBrand size="sm" />
        <p className="text-white mt-2">{content.differentiator}</p>
      </motion.div>
    </div>
  );
}

// === ARCHITECTURE SLIDES ===

function ArchitectureSlide({
  content,
}: {
  content: ExtractContent<"architecture">;
}) {
  return (
    <div className="max-w-6xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-16 font-mono"
      >
        How It Works
      </motion.h2>

      {/* Pipeline visualization - single row */}
      <div className="flex flex-nowrap items-center justify-center gap-4">
        {/* Input files on the left - inline */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col items-center p-4 rounded-xl border border-zinc-600 bg-zinc-800/80"
        >
          <span className="text-lg font-bold text-zinc-300">.mp4 / .dem</span>
          <span className="text-xs text-zinc-500 mt-1">Video + Replay</span>
        </motion.div>

        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="text-amber-500 text-2xl"
        >
          →
        </motion.span>

        {content.pipeline.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 + i * 0.15 }}
            className="flex items-center gap-4"
          >
            <div
              className="flex flex-col items-center p-4 rounded-xl border border-amber-500/40 bg-zinc-900/80"
              style={{ boxShadow: "0 0 25px rgba(245, 158, 11, 0.15)" }}
            >
              <span className="text-lg font-bold text-amber-400">
                {item.step}
              </span>
              <span className="text-xs text-zinc-500 mt-1">{item.detail}</span>
            </div>
            {i < content.pipeline.length - 1 && (
              <span className="text-amber-500 text-2xl">→</span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function ArchitectureGeminiSlide({
  content,
}: {
  content: ExtractContent<"architecture-gemini">;
}) {
  return (
    <div className="max-w-5xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-4 font-mono"
      >
        Powered by Gemini
      </motion.h2>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-zinc-400 text-center mb-12"
      >
        What makes this possible
      </motion.p>

      {/* Pipeline - smaller version */}
      <div className="flex flex-wrap items-center justify-center gap-3 mb-12">
        {/* Input files on the left */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col gap-2"
        >
          <div className="flex flex-col items-center px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-800/80 min-w-[70px]">
            <span className="text-xs font-bold text-zinc-400">.mp4</span>
          </div>
          <div className="flex flex-col items-center px-3 py-1.5 rounded-md border border-zinc-700 bg-zinc-800/80 min-w-[70px]">
            <span className="text-xs font-bold text-zinc-400">.dem</span>
          </div>
        </motion.div>

        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15 }}
          className="text-zinc-600 text-lg"
        >
          →
        </motion.span>

        {content.pipelineSteps.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.08 }}
            className="flex items-center gap-3"
          >
            <div className="flex flex-col items-center px-4 py-2 rounded-lg border border-zinc-700 bg-zinc-900/60 min-w-[100px]">
              <span className="text-sm font-bold text-zinc-300">
                {item.step}
              </span>
              <span className="text-xs text-zinc-600">{item.detail}</span>
            </div>
            {i < content.pipelineSteps.length - 1 && (
              <span className="text-zinc-600 text-lg">→</span>
            )}
          </motion.div>
        ))}
      </div>

      {/* Gemini Features - prominent */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="p-6 rounded-2xl border-2 border-amber-500/50 bg-amber-500/5"
        style={{ boxShadow: "0 0 40px rgba(245, 158, 11, 0.15)" }}
      >
        <div className="flex items-center gap-2 mb-6">
          <span className="text-2xl font-bold text-amber-500 font-mono">
            GEMINI
          </span>
          <span className="text-zinc-400">Features</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {content.geminiFeatures.map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.6 + i * 0.1 }}
              className="flex flex-col items-center p-4 rounded-xl bg-zinc-900/80 border border-amber-500/30"
            >
              <span className="text-lg font-bold text-amber-400">
                {feature.step}
              </span>
              <span className="text-xs text-zinc-500 mt-1 text-center">
                {feature.detail}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

// === ARCHITECTURE GEMINI FLOW SLIDES ===

function FlowNode({
  label,
  detail,
  color = "zinc",
  delay = 0,
  badge,
  size = "md",
}: {
  label: string;
  detail?: string;
  color?: "amber" | "zinc" | "blue" | "green" | "purple";
  delay?: number;
  badge?: string;
  size?: "sm" | "md" | "lg";
}) {
  const colorMap = {
    amber: "border-amber-500/60 bg-amber-500/10 text-amber-400",
    zinc: "border-zinc-600 bg-zinc-800/80 text-zinc-300",
    blue: "border-blue-500/50 bg-blue-500/10 text-blue-400",
    green: "border-green-500/50 bg-green-500/10 text-green-400",
    purple: "border-purple-500/50 bg-purple-500/10 text-purple-400",
  };
  const sizeMap = {
    sm: "px-3 py-2 min-w-[80px]",
    md: "px-5 py-3 min-w-[120px]",
    lg: "px-6 py-4 min-w-[150px]",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      className="relative flex flex-col items-center"
    >
      <div
        className={`relative rounded-xl border-2 ${colorMap[color]} ${sizeMap[size]} text-center`}
        style={
          color === "amber"
            ? { boxShadow: "0 0 20px rgba(245, 158, 11, 0.15)" }
            : undefined
        }
      >
        <span className="font-bold text-sm">{label}</span>
        {detail && (
          <span className="block text-[10px] text-zinc-500 mt-0.5">
            {detail}
          </span>
        )}
      </div>
      {badge && (
        <motion.span
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: delay + 0.3 }}
          className="absolute -bottom-5 px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-[9px] text-amber-400 font-mono whitespace-nowrap"
        >
          {badge}
        </motion.span>
      )}
    </motion.div>
  );
}

function FlowArrow({
  direction = "right",
  label,
  delay = 0,
  color = "zinc",
}: {
  direction?: "right" | "down" | "left";
  label?: string;
  delay?: number;
  color?: "amber" | "zinc" | "green";
}) {
  const arrows = { right: "→", down: "↓", left: "←" };
  const colorMap = {
    amber: "text-amber-500",
    zinc: "text-zinc-600",
    green: "text-green-500",
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay }}
      className={`flex flex-col items-center gap-0.5 ${direction === "down" ? "my-1" : "mx-1"}`}
    >
      {label && (
        <span className="text-[9px] text-zinc-500 font-mono">{label}</span>
      )}
      <span className={`text-xl ${colorMap[color]}`}>{arrows[direction]}</span>
    </motion.div>
  );
}

function ArchitectureGeminiFlowSlide({
  content,
}: {
  content: ExtractContent<"architecture-gemini-flow">;
}) {
  if (content.variant === 3) return <GeminiFlowVariant3 />;
  if (content.variant === 4) return <GeminiFlowInteractive />;
  if (content.variant === 5) return <GeminiFlowIngest />;
  if (content.variant === 6) return <GeminiFlowAgents />;
  if (content.variant === 7) return <GeminiFlowSimple />;
  return null;
}

// Variant 3: Horizontal Sequential Flow with Feature Badges
function GeminiFlowVariant3() {
  const steps = [
    { label: "Upload", detail: "Video + Replay", color: "zinc" as const, badge: null, arrow: "files" },
    { label: "File API", detail: "Process video", color: "amber" as const, badge: "700MB / 30min", arrow: "video URI" },
    { label: "Observer", detail: "Analyze gameplay", color: "blue" as const, badge: "Thinking: HIGH", arrow: "interaction_id" },
    { label: "Validator", detail: "Verify tips", color: "purple" as const, badge: "Interactions API", arrow: "verified tips" },
    { label: "Output", detail: "JSON tips", color: "green" as const, badge: "Structured Output", arrow: null },
  ];

  return (
    <div className="max-w-6xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-3 font-mono"
      >
        Powered by Gemini
      </motion.h2>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-zinc-500 text-center mb-14 text-sm"
      >
        Data flow through the analysis pipeline
      </motion.p>

      <div className="flex items-start justify-center gap-1">
        {steps.map((step, i) => (
          <div key={i} className="flex items-start">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.12 }}
              className="flex flex-col items-center"
            >
              <div
                className={`relative rounded-xl border-2 px-5 py-4 min-w-[110px] text-center ${
                  step.color === "amber"
                    ? "border-amber-500/60 bg-amber-500/10"
                    : step.color === "blue"
                      ? "border-blue-500/50 bg-blue-500/10"
                      : step.color === "purple"
                        ? "border-purple-500/50 bg-purple-500/10"
                        : step.color === "green"
                          ? "border-green-500/50 bg-green-500/10"
                          : "border-zinc-600 bg-zinc-800/80"
                }`}
                style={
                  step.color === "amber"
                    ? { boxShadow: "0 0 25px rgba(245, 158, 11, 0.12)" }
                    : undefined
                }
              >
                <span
                  className={`font-bold text-sm ${
                    step.color === "amber"
                      ? "text-amber-400"
                      : step.color === "blue"
                        ? "text-blue-400"
                        : step.color === "purple"
                          ? "text-purple-400"
                          : step.color === "green"
                            ? "text-green-400"
                            : "text-zinc-300"
                  }`}
                >
                  {step.label}
                </span>
                <span className="block text-[10px] text-zinc-500 mt-1">
                  {step.detail}
                </span>
              </div>

              {step.badge && (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.12 }}
                  className="mt-3 px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[9px] text-amber-400 font-mono whitespace-nowrap"
                >
                  {step.badge}
                </motion.div>
              )}
            </motion.div>

            {step.arrow && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 + i * 0.12 }}
                className="flex flex-col items-center mx-2 pt-5"
              >
                <span className="text-[8px] text-zinc-600 font-mono mb-0.5 whitespace-nowrap">
                  {step.arrow}
                </span>
                <span className="text-lg text-amber-500/60">→</span>
              </motion.div>
            )}
          </div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="mt-12 flex justify-center"
      >
        <div className="flex items-center gap-4 px-6 py-3 rounded-xl border border-zinc-700/50 bg-zinc-900/50">
          <span className="text-xs text-zinc-500">Throughout the pipeline:</span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
            Multimodal: Video + Replay + Text
          </span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
            Long Context: Full match
          </span>
        </div>
      </motion.div>
    </div>
  );
}

// Variant 4: Interactive Step-Through Architecture
// Boxes visible from the start, arrows revealed one phase at a time
// with Space/ArrowRight. Intercepts keyboard to prevent slide advance.
function GeminiFlowInteractive() {
  // Step phases (grouped arrows)
  const phases = [
    { label: "Upload files", description: "Frontend uploads video + replay to GCS via signed URLs" },
    { label: "Parse replay", description: "Backend downloads replay from GCS, parses player data" },
    { label: "Start analysis", description: "Frontend sends analysis request, Backend writes to Firestore" },
    { label: "Upload to Gemini", description: "Backend downloads video from GCS, uploads to Gemini File API" },
    { label: "Observer analyzes", description: "Observer agent sends video + replay to Gemini Interactions API (Thinking: HIGH)" },
    { label: "Validator verifies", description: "Validator chains from Observer interaction, cross-checks tips against video" },
    { label: "Post-processing", description: "Backend generates thumbnail, writes results to Firestore" },
    { label: "Results loaded", description: "Frontend polls Firestore status, fetches complete analysis with signed URLs" },
    { label: "Chat", description: "Chat chains from Validator interaction — full pipeline context without re-sending video" },
  ];

  const [step, setStep] = useState(0);
  const totalSteps = phases.length;

  const advance = useCallback(() => {
    setStep((s) => Math.min(s + 1, totalSteps));
  }, [totalSteps]);

  const goBack = useCallback(() => {
    setStep((s) => Math.max(s - 1, 0));
  }, []);

  // Intercept keyboard: consume Space/ArrowRight/ArrowDown when steps remain,
  // consume ArrowLeft/ArrowUp when steps > 0 (to go back through steps)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (
        e.code === "ArrowRight" ||
        e.code === "ArrowDown" ||
        e.code === "Space"
      ) {
        if (step < totalSteps) {
          e.stopPropagation();
          advance();
        }
        // else: let event bubble to SlideViewer to go to next slide
      } else if (e.code === "ArrowLeft" || e.code === "ArrowUp") {
        if (step > 0) {
          e.stopPropagation();
          goBack();
        }
        // else: let event bubble to SlideViewer to go to prev slide
      }
    };

    // Use capture phase so we intercept before SlideViewer
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [step, totalSteps, advance, goBack]);

  // Node positions (percentages of container) — laid out like the handwriting
  // Left column: Frontend, Firestore
  // Center-left: GCS Bucket
  // Center: Backend, Parser
  // Center-right: Agents (Observer, Validator)
  // Right: Gemini APIs

  const show = (minStep: number) => step >= minStep;
  const arrowOpacity = (minStep: number) =>
    step >= minStep ? "opacity-100" : "opacity-0";
  const arrowTransition = "transition-opacity duration-500";

  return (
    <div className="max-w-[1100px] w-full h-[520px] relative">
      {/* Title */}
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl md:text-4xl font-bold text-white text-center mb-1 font-mono"
      >
        Powered by Gemini
      </motion.h2>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="text-zinc-600 text-center mb-4 text-xs"
      >
        Press <span className="font-mono text-zinc-500">Space</span> to step through the pipeline
      </motion.p>

      {/* Flow container — all boxes visible, arrows appear */}
      <div className="relative w-full h-[400px]">
        {/* === BOXES (always visible) === */}

        {/* Frontend */}
        <div className="absolute left-0 top-[45%] -translate-y-1/2">
          <Box label="Frontend" color="green" icon="🎮" />
        </div>

        {/* GCS Bucket */}
        <div className="absolute left-[17%] top-[8%]">
          <Box label="GCS Bucket" color="zinc" icon="☁️" size="sm" />
        </div>

        {/* Firestore */}
        <div className="absolute left-[15%] top-[82%]">
          <Box label="Firestore" color="zinc" icon="🗄️" size="sm" />
        </div>

        {/* Backend */}
        <div className="absolute left-[38%] top-[45%] -translate-y-1/2">
          <Box label="Backend" color="amber" icon="⚡" />
        </div>

        {/* Parser */}
        <div className="absolute left-[40%] top-[80%]">
          <Box label="Parser" color="zinc" icon="📋" size="sm" sub="AoE2 / CS2" />
        </div>

        {/* Agents box with Observer + Validator inside */}
        <div className="absolute left-[55%] top-[2%]">
          <div className="rounded-xl border-2 border-blue-500/40 bg-blue-500/5 px-4 py-3 min-w-[140px]">
            <span className="text-[10px] text-blue-400/60 font-mono block mb-2">Agents</span>
            <div className="space-y-2">
              <div className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400 text-center font-bold">
                Observer
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/30 text-xs text-purple-400 text-center font-bold">
                Validator
              </div>
            </div>
          </div>
        </div>

        {/* Gemini APIs */}
        <div className="absolute right-0 top-[5%]">
          <div className="rounded-xl border-2 border-amber-500/40 bg-amber-500/5 px-4 py-3 min-w-[130px]"
            style={{ boxShadow: "0 0 25px rgba(245, 158, 11, 0.1)" }}>
            <span className="text-sm font-bold text-amber-400 font-mono block mb-2">Gemini</span>
            <div className="space-y-1.5">
              <div className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 text-center">
                File API
              </div>
              <div className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 text-center">
                Interactions API
              </div>
              <div className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 text-center">
                Thinking
              </div>
              <div className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 text-center">
                Structured Output
              </div>
            </div>
          </div>
        </div>

        {/* === ARROWS (revealed step by step) === */}
        {/* Using SVG overlay for curved/angled arrows */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 1100 400">
          <defs>
            <marker id="ah-amber" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="rgb(245, 158, 11)" fillOpacity="0.7" />
            </marker>
            <marker id="ah-green" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="rgb(34, 197, 94)" fillOpacity="0.7" />
            </marker>
            <marker id="ah-blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="rgb(96, 165, 250)" fillOpacity="0.7" />
            </marker>
            <marker id="ah-purple" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="rgb(168, 85, 247)" fillOpacity="0.7" />
            </marker>
            <marker id="ah-zinc" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="rgb(161, 161, 170)" fillOpacity="0.7" />
            </marker>
          </defs>

          {/* Step 1: Frontend → GCS (upload video + replay) */}
          <g className={`${arrowTransition} ${arrowOpacity(1)}`}>
            <path d="M 95 155 Q 140 60 200 55" fill="none" stroke="rgb(34, 197, 94)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-green)" />
            <text x="105" y="85" fill="rgb(161,161,170)" fontSize="9" fontFamily="monospace">.mp4 + .dem</text>
            <circle cx="120" cy="100" r="9" fill="rgb(24,24,27)" stroke="rgb(34, 197, 94)" strokeWidth="1.5" strokeOpacity="0.6" />
            <text x="120" y="103" fill="rgb(34, 197, 94)" fontSize="8" textAnchor="middle" fontWeight="bold">1</text>
          </g>

          {/* Step 2: GCS → Backend (download replay), Backend → Parser */}
          <g className={`${arrowTransition} ${arrowOpacity(2)}`}>
            {/* GCS → Backend */}
            <path d="M 260 65 Q 370 50 415 150" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-zinc)" />
            <text x="310" y="85" fill="rgb(161,161,170)" fontSize="9" fontFamily="monospace">replay</text>
            {/* Backend → Parser */}
            <path d="M 450 220 L 460 300" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-zinc)" />
            {/* Parser → Backend */}
            <path d="M 475 300 L 470 220" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" strokeDasharray="4 3" markerEnd="url(#ah-zinc)" />
            <text x="480" y="270" fill="rgb(161,161,170)" fontSize="8" fontFamily="monospace">players</text>
            <circle cx="350" cy="60" r="9" fill="rgb(24,24,27)" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" />
            <text x="350" y="63" fill="rgb(161,161,170)" fontSize="8" textAnchor="middle" fontWeight="bold">2</text>
          </g>

          {/* Step 3: Frontend → Backend (start analysis), Backend → Firestore */}
          <g className={`${arrowTransition} ${arrowOpacity(3)}`}>
            {/* Frontend → Backend */}
            <path d="M 100 195 L 400 195" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-amber)" />
            <text x="200" y="190" fill="rgb(245, 158, 11)" fontSize="9" fontFamily="monospace">POST /analysis</text>
            {/* Backend → Firestore */}
            <path d="M 420 220 Q 340 330 230 345" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-zinc)" />
            <text x="280" y="310" fill="rgb(161,161,170)" fontSize="8" fontFamily="monospace">status: processing</text>
            <circle cx="250" cy="195" r="9" fill="rgb(24,24,27)" stroke="rgb(245, 158, 11)" strokeWidth="1.5" strokeOpacity="0.6" />
            <text x="250" y="198" fill="rgb(245, 158, 11)" fontSize="8" textAnchor="middle" fontWeight="bold">3</text>
          </g>

          {/* Step 4: Backend → GCS (download video), Backend → Gemini File API */}
          <g className={`${arrowTransition} ${arrowOpacity(4)}`}>
            {/* GCS → Backend (download video) */}
            <path d="M 250 70 Q 350 120 415 165" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-zinc)" />
            <text x="280" y="120" fill="rgb(161,161,170)" fontSize="8" fontFamily="monospace">video download</text>
            {/* Backend → Gemini File API */}
            <path d="M 490 155 Q 700 30 900 55" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-amber)" />
            <text x="680" y="30" fill="rgb(245, 158, 11)" fontSize="9" fontFamily="monospace">upload video</text>
            <circle cx="700" cy="50" r="9" fill="rgb(24,24,27)" stroke="rgb(245, 158, 11)" strokeWidth="1.5" strokeOpacity="0.6" />
            <text x="700" y="53" fill="rgb(245, 158, 11)" fontSize="8" textAnchor="middle" fontWeight="bold">4</text>
          </g>

          {/* Step 5: Backend → Observer, Observer → Gemini Interactions API */}
          <g className={`${arrowTransition} ${arrowOpacity(5)}`}>
            {/* Backend → Observer */}
            <path d="M 470 150 Q 530 80 610 40" fill="none" stroke="rgb(96, 165, 250)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-blue)" />
            <text x="510" y="72" fill="rgb(96, 165, 250)" fontSize="8" fontFamily="monospace">video + replay</text>
            {/* Observer → Gemini */}
            <path d="M 735 30 L 890 75" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-amber)" />
            <text x="770" y="44" fill="rgb(245, 158, 11)" fontSize="8" fontFamily="monospace">Thinking: HIGH</text>
            <circle cx="790" cy="30" r="9" fill="rgb(24,24,27)" stroke="rgb(96, 165, 250)" strokeWidth="1.5" strokeOpacity="0.6" />
            <text x="790" y="33" fill="rgb(96, 165, 250)" fontSize="8" textAnchor="middle" fontWeight="bold">5</text>
          </g>

          {/* Step 6: Observer → Validator (interaction_id chain), Validator → Gemini */}
          <g className={`${arrowTransition} ${arrowOpacity(6)}`}>
            {/* Observer → Validator (internal) */}
            <path d="M 665 55 L 665 75" fill="none" stroke="rgb(168, 85, 247)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-purple)" />
            {/* Validator → Gemini (chained) */}
            <path d="M 735 90 L 890 95" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-amber)" />
            <text x="755" y="110" fill="rgb(168, 85, 247)" fontSize="8" fontFamily="monospace">chains interaction_id</text>
            <circle cx="785" cy="90" r="9" fill="rgb(24,24,27)" stroke="rgb(168, 85, 247)" strokeWidth="1.5" strokeOpacity="0.6" />
            <text x="785" y="93" fill="rgb(168, 85, 247)" fontSize="8" textAnchor="middle" fontWeight="bold">6</text>
          </g>

          {/* Step 7: Backend → GCS (thumbnail), Backend → Firestore (complete) */}
          <g className={`${arrowTransition} ${arrowOpacity(7)}`}>
            {/* Agents → Backend (results) */}
            <path d="M 610 105 Q 550 150 490 170" fill="none" stroke="rgb(34, 197, 94)" strokeWidth="2" strokeOpacity="0.5" strokeDasharray="4 3" markerEnd="url(#ah-green)" />
            <text x="520" y="145" fill="rgb(34, 197, 94)" fontSize="8" fontFamily="monospace">verified tips (JSON)</text>
            {/* Backend → GCS (thumbnail) */}
            <path d="M 430 150 Q 320 40 250 50" fill="none" stroke="rgb(161,161,170)" strokeWidth="1.5" strokeOpacity="0.4" markerEnd="url(#ah-zinc)" />
            <text x="310" y="38" fill="rgb(161,161,170)" fontSize="7" fontFamily="monospace">thumbnail</text>
            {/* Backend → Firestore */}
            <path d="M 440 220 Q 360 340 230 350" fill="none" stroke="rgb(34, 197, 94)" strokeWidth="2" strokeOpacity="0.5" markerEnd="url(#ah-green)" />
            <text x="345" y="340" fill="rgb(34, 197, 94)" fontSize="8" fontFamily="monospace">status: complete</text>
            <circle cx="430" cy="130" r="9" fill="rgb(24,24,27)" stroke="rgb(34, 197, 94)" strokeWidth="1.5" strokeOpacity="0.5" />
            <text x="430" y="133" fill="rgb(34, 197, 94)" fontSize="8" textAnchor="middle" fontWeight="bold">7</text>
          </g>

          {/* Step 8: Firestore → Frontend (poll), Backend → Frontend (signed URLs + data) */}
          <g className={`${arrowTransition} ${arrowOpacity(8)}`}>
            {/* Firestore → Frontend (poll status) */}
            <path d="M 180 350 Q 100 340 75 220" fill="none" stroke="rgb(34, 197, 94)" strokeWidth="2" strokeOpacity="0.5" strokeDasharray="4 3" markerEnd="url(#ah-green)" />
            <text x="60" y="300" fill="rgb(34, 197, 94)" fontSize="8" fontFamily="monospace">poll status</text>
            {/* Backend → Frontend (full results) */}
            <path d="M 400 210 L 100 210" fill="none" stroke="rgb(34, 197, 94)" strokeWidth="2" strokeOpacity="0.6" markerEnd="url(#ah-green)" />
            <text x="180" y="228" fill="rgb(34, 197, 94)" fontSize="8" fontFamily="monospace">tips + signed video URL</text>
            <circle cx="250" cy="210" r="9" fill="rgb(24,24,27)" stroke="rgb(34, 197, 94)" strokeWidth="1.5" strokeOpacity="0.5" />
            <text x="250" y="213" fill="rgb(34, 197, 94)" fontSize="8" textAnchor="middle" fontWeight="bold">8</text>
          </g>

          {/* Step 9: Frontend → Backend (chat), Backend → Gemini (chained from validator) */}
          <g className={`${arrowTransition} ${arrowOpacity(9)}`}>
            {/* Frontend → Backend (chat) */}
            <path d="M 100 230 L 400 230" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-amber)" />
            <text x="170" y="248" fill="rgb(245, 158, 11)" fontSize="8" fontFamily="monospace">POST /chat</text>
            {/* Backend → Gemini (chained interaction) */}
            <path d="M 490 185 Q 700 145 890 120" fill="none" stroke="rgb(245, 158, 11)" strokeWidth="1.5" strokeOpacity="0.5" markerEnd="url(#ah-amber)" />
            <text x="680" y="140" fill="rgb(245, 158, 11)" fontSize="8" fontFamily="monospace">chains from pipeline</text>
            <circle cx="690" cy="160" r="9" fill="rgb(24,24,27)" stroke="rgb(245, 158, 11)" strokeWidth="1.5" strokeOpacity="0.5" />
            <text x="690" y="163" fill="rgb(245, 158, 11)" fontSize="8" textAnchor="middle" fontWeight="bold">9</text>
          </g>
        </svg>
      </div>

      {/* Step indicator + description */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-3">
          {/* Step dots */}
          <div className="flex gap-1.5">
            {phases.map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  i < step
                    ? "bg-amber-500"
                    : i === step
                      ? "bg-amber-500/50 ring-1 ring-amber-500/50"
                      : "bg-zinc-700"
                }`}
              />
            ))}
          </div>
          <span className="text-zinc-600 text-xs font-mono">
            {step}/{totalSteps}
          </span>
        </div>

        {/* Current phase description */}
        <div className="text-right">
          {step > 0 && step <= totalSteps && (
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2"
            >
              <span className="text-amber-400 text-xs font-bold">
                {phases[step - 1].label}
              </span>
              <span className="text-zinc-500 text-xs">
                {phases[step - 1].description}
              </span>
            </motion.div>
          )}
          {step === 0 && (
            <span className="text-zinc-600 text-xs italic">
              Press Space to begin
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// Shared box component for the interactive flow
function Box({
  label,
  color,
  icon,
  size = "md",
  sub,
}: {
  label: string;
  color: "amber" | "green" | "zinc" | "blue";
  icon?: string;
  size?: "sm" | "md";
  sub?: string;
}) {
  const colors = {
    amber: "border-amber-500/50 bg-amber-500/5",
    green: "border-green-500/40 bg-green-500/5",
    zinc: "border-zinc-600 bg-zinc-800/60",
    blue: "border-blue-500/40 bg-blue-500/5",
  };
  const textColors = {
    amber: "text-amber-400",
    green: "text-green-400",
    zinc: "text-zinc-400",
    blue: "text-blue-400",
  };

  return (
    <div
      className={`rounded-xl border-2 ${colors[color]} ${size === "sm" ? "px-3 py-2" : "px-5 py-3"} text-center`}
      style={
        color === "amber"
          ? { boxShadow: "0 0 20px rgba(245, 158, 11, 0.1)" }
          : undefined
      }
    >
      {icon && <span className="text-lg block mb-0.5">{icon}</span>}
      <span className={`font-bold ${size === "sm" ? "text-xs" : "text-sm"} ${textColors[color]}`}>
        {label}
      </span>
      {sub && (
        <span className="block text-[9px] text-zinc-600 mt-0.5">{sub}</span>
      )}
    </div>
  );
}

// Variant 5: Ingest slide (Part 1 of 2)
// Interactive, 3 steps: Upload → Parse → File API
function GeminiFlowIngest() {
  const phases = [
    { label: "Upload", description: "Video (.mp4) and replay (.dem) uploaded to cloud storage" },
    { label: "Parse", description: "Replay parsed for players, rounds, kills, economy data" },
    { label: "Gemini File API", description: "Video uploaded to Gemini — up to 700MB, 30-minute matches" },
  ];

  const [step, setStep] = useState(0);
  const totalSteps = phases.length;

  const advance = useCallback(() => {
    setStep((s) => Math.min(s + 1, totalSteps));
  }, [totalSteps]);

  const goBack = useCallback(() => {
    setStep((s) => Math.max(s - 1, 0));
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === "ArrowRight" || e.code === "ArrowDown" || e.code === "Space") {
        if (step < totalSteps) { e.stopPropagation(); advance(); }
      } else if (e.code === "ArrowLeft" || e.code === "ArrowUp") {
        if (step > 0) { e.stopPropagation(); goBack(); }
      }
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [step, totalSteps, advance, goBack]);

  const show = (s: number) => step >= s;
  const t = "transition-all duration-500";

  return (
    <div className="max-w-5xl w-full">
      <motion.h2 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-2 font-mono">
        Powered by Gemini
      </motion.h2>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="text-zinc-500 text-center mb-2 text-sm">
        Step 1: Ingest
      </motion.p>
      <p className="text-zinc-700 text-center mb-10 text-xs">
        Press <span className="font-mono text-zinc-500">Space</span> to step through
      </p>

      {/* Flow: User → GCS → Backend/Parser → Gemini File API */}
      <div className="flex items-center justify-center gap-3">
        {/* User */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
          className="rounded-xl border-2 border-green-500/40 bg-green-500/5 px-5 py-4 text-center">
          <span className="text-2xl block mb-1">🎮</span>
          <span className="text-sm font-bold text-green-400">User</span>
          <span className="block text-[10px] text-zinc-600 mt-1">.mp4 + .dem</span>
        </motion.div>

        {/* Arrow 1: Upload */}
        <div className={`${t} ${show(1) ? "opacity-100" : "opacity-0"} flex flex-col items-center mx-1`}>
          <span className="text-[9px] text-zinc-500 font-mono">upload</span>
          <span className="text-xl text-green-500/60">→</span>
        </div>

        {/* GCS + Backend/Parser */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          className="flex flex-col items-center gap-3">
          <div className="rounded-xl border-2 border-zinc-600 bg-zinc-800/60 px-5 py-3 text-center">
            <span className="text-lg block mb-0.5">☁️</span>
            <span className="text-xs font-bold text-zinc-400">GCS</span>
          </div>
          {/* Arrow down to parser (step 2) */}
          <div className={`${t} ${show(2) ? "opacity-100" : "opacity-0"} flex flex-col items-center`}>
            <span className="text-lg text-zinc-600">↓</span>
          </div>
          <div className={`${t} ${show(2) ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}>
            <div className="rounded-xl border-2 border-amber-500/40 bg-amber-500/5 px-5 py-3 text-center">
              <span className="text-lg block mb-0.5">⚡</span>
              <span className="text-xs font-bold text-amber-400">Backend</span>
              <span className="block text-[9px] text-zinc-600 mt-1">Parse replay data</span>
            </div>
          </div>
        </motion.div>

        {/* Arrow 3: To Gemini */}
        <div className={`${t} ${show(3) ? "opacity-100" : "opacity-0"} flex flex-col items-center mx-1`}>
          <span className="text-[9px] text-amber-500 font-mono">video</span>
          <span className="text-xl text-amber-500/60">→</span>
        </div>

        {/* Gemini File API */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
          className="rounded-xl border-2 border-amber-500/50 bg-amber-500/5 px-6 py-4 text-center"
          style={{ boxShadow: "0 0 25px rgba(245, 158, 11, 0.12)" }}>
          <span className="text-sm font-bold text-amber-400 font-mono">Gemini</span>
          <div className="mt-2 px-3 py-1.5 rounded bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400">
            File API
          </div>
          <span className="block text-[9px] text-zinc-600 mt-2">700MB / 30min</span>
        </motion.div>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-between mt-10">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            {phases.map((_, i) => (
              <div key={i} className={`w-2 h-2 rounded-full ${t} ${i < step ? "bg-amber-500" : "bg-zinc-700"}`} />
            ))}
          </div>
          <span className="text-zinc-600 text-xs font-mono">{step}/{totalSteps}</span>
        </div>
        {step > 0 && step <= totalSteps && (
          <motion.span key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-zinc-500 text-xs">
            {phases[step - 1].description}
          </motion.span>
        )}
      </div>
    </div>
  );
}

// Variant 6: Agents slide (Part 2 of 2)
// Interactive, 3 steps: Observer → Validator (chained) → Output
function GeminiFlowAgents() {
  const phases = [
    { label: "Observer", description: "Multi-angle gameplay analysis with Thinking: HIGH" },
    { label: "Validator", description: "Chains from Observer interaction — video already in context" },
    { label: "Output", description: "Structured Output enforces JSON schema for the frontend" },
  ];

  const [step, setStep] = useState(0);
  const totalSteps = phases.length;

  const advance = useCallback(() => {
    setStep((s) => Math.min(s + 1, totalSteps));
  }, [totalSteps]);

  const goBack = useCallback(() => {
    setStep((s) => Math.max(s - 1, 0));
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.code === "ArrowRight" || e.code === "ArrowDown" || e.code === "Space") {
        if (step < totalSteps) { e.stopPropagation(); advance(); }
      } else if (e.code === "ArrowLeft" || e.code === "ArrowUp") {
        if (step > 0) { e.stopPropagation(); goBack(); }
      }
    };
    window.addEventListener("keydown", handler, true);
    return () => window.removeEventListener("keydown", handler, true);
  }, [step, totalSteps, advance, goBack]);

  const show = (s: number) => step >= s;
  const t = "transition-all duration-500";

  return (
    <div className="max-w-5xl w-full">
      <motion.h2 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-2 font-mono">
        Powered by Gemini
      </motion.h2>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="text-zinc-500 text-center mb-2 text-sm">
        Step 2: Analyze
      </motion.p>
      <p className="text-zinc-700 text-center mb-10 text-xs">
        Press <span className="font-mono text-zinc-500">Space</span> to step through
      </p>

      <div className="flex items-start justify-center gap-4">
        {/* Observer */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
          className="flex flex-col items-center">
          <div className="rounded-xl border-2 border-blue-500/50 bg-blue-500/10 px-6 py-5 text-center min-w-[140px]">
            <span className="text-sm font-bold text-blue-400">Observer</span>
            <span className="block text-[10px] text-zinc-500 mt-1">Multi-angle analysis</span>
          </div>
          {/* Gemini badge */}
          <div className={`${t} ${show(1) ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"} mt-3 flex flex-col items-center gap-1.5`}>
            <div className="px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
              Thinking: HIGH
            </div>
            <div className="px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
              Multimodal
            </div>
          </div>
        </motion.div>

        {/* Arrow: interaction_id chain */}
        <div className={`${t} ${show(2) ? "opacity-100" : "opacity-0"} flex flex-col items-center mt-6 mx-2`}>
          <span className="text-[9px] text-purple-400 font-mono mb-1">interaction_id</span>
          <span className="text-2xl text-amber-500/60">→</span>
          <span className="text-[9px] text-zinc-600 font-mono mt-1">context chained</span>
        </div>

        {/* Validator */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
          className="flex flex-col items-center">
          <div className="rounded-xl border-2 border-purple-500/50 bg-purple-500/10 px-6 py-5 text-center min-w-[140px]">
            <span className="text-sm font-bold text-purple-400">Validator</span>
            <span className="block text-[10px] text-zinc-500 mt-1">Cross-check & score</span>
          </div>
          {/* Gemini badge */}
          <div className={`${t} ${show(2) ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"} mt-3 flex flex-col items-center gap-1.5`}>
            <div className="px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
              Interactions API
            </div>
            <div className="px-3 py-1 rounded-full bg-zinc-700/50 border border-zinc-600 text-[10px] text-zinc-500 font-mono">
              Video in server context
            </div>
          </div>
        </motion.div>

        {/* Arrow: output */}
        <div className={`${t} ${show(3) ? "opacity-100" : "opacity-0"} flex flex-col items-center mt-6 mx-2`}>
          <span className="text-[9px] text-green-400 font-mono mb-1">verified JSON</span>
          <span className="text-2xl text-green-500/60">→</span>
        </div>

        {/* Output */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}
          className="flex flex-col items-center">
          <div className="rounded-xl border-2 border-green-500/50 bg-green-500/10 px-6 py-5 text-center min-w-[140px]">
            <span className="text-sm font-bold text-green-400">Coaching Tips</span>
            <span className="block text-[10px] text-zinc-500 mt-1">Timestamped & scored</span>
          </div>
          <div className={`${t} ${show(3) ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-2"} mt-3`}>
            <div className="px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
              Structured Output
            </div>
          </div>
        </motion.div>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-between mt-12">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            {phases.map((_, i) => (
              <div key={i} className={`w-2 h-2 rounded-full ${t} ${i < step ? "bg-amber-500" : "bg-zinc-700"}`} />
            ))}
          </div>
          <span className="text-zinc-600 text-xs font-mono">{step}/{totalSteps}</span>
        </div>
        {step > 0 && step <= totalSteps && (
          <motion.span key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-zinc-500 text-xs">
            {phases[step - 1].description}
          </motion.span>
        )}
      </div>
    </div>
  );
}

// Variant 7: Simplified single-slide overview (no stepping)
// 4 boxes in a row with Gemini features underneath each
function GeminiFlowSimple() {
  const nodes = [
    { label: "File API", detail: "Ingest video", color: "amber" as const, feature: "700MB / 30min", arrow: "video URI" },
    { label: "Observer", detail: "Analyze gameplay", color: "blue" as const, feature: "Thinking: HIGH", arrow: "interaction_id" },
    { label: "Validator", detail: "Verify tips", color: "purple" as const, feature: "Interactions API", arrow: "JSON" },
    { label: "Tips", detail: "Coaching output", color: "green" as const, feature: "Structured Output", arrow: null },
  ];

  return (
    <div className="max-w-5xl w-full">
      <motion.h2 initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}
        className="text-4xl md:text-5xl font-bold text-white text-center mb-3 font-mono">
        Powered by Gemini
      </motion.h2>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="text-zinc-500 text-center mb-14 text-sm">
        Analysis pipeline
      </motion.p>

      <div className="flex items-start justify-center gap-2">
        {nodes.map((node, i) => (
          <div key={i} className="flex items-start">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.12 }} className="flex flex-col items-center">
              <div className={`rounded-xl border-2 px-6 py-5 text-center min-w-[130px] ${
                node.color === "amber" ? "border-amber-500/60 bg-amber-500/10" :
                node.color === "blue" ? "border-blue-500/50 bg-blue-500/10" :
                node.color === "purple" ? "border-purple-500/50 bg-purple-500/10" :
                "border-green-500/50 bg-green-500/10"
              }`} style={node.color === "amber" ? { boxShadow: "0 0 20px rgba(245, 158, 11, 0.1)" } : undefined}>
                <span className={`font-bold text-sm ${
                  node.color === "amber" ? "text-amber-400" :
                  node.color === "blue" ? "text-blue-400" :
                  node.color === "purple" ? "text-purple-400" : "text-green-400"
                }`}>{node.label}</span>
                <span className="block text-[10px] text-zinc-500 mt-1">{node.detail}</span>
              </div>
              <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + i * 0.12 }}
                className="mt-3 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
                {node.feature}
              </motion.div>
            </motion.div>

            {node.arrow && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 0.3 + i * 0.12 }}
                className="flex flex-col items-center mx-2 mt-7">
                <span className="text-[9px] text-zinc-600 font-mono mb-0.5">{node.arrow}</span>
                <span className="text-xl text-amber-500/50">→</span>
              </motion.div>
            )}
          </div>
        ))}
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
        className="mt-12 flex justify-center">
        <div className="flex items-center gap-4 px-6 py-3 rounded-xl border border-zinc-700/50 bg-zinc-900/50">
          <span className="text-xs text-zinc-500">Throughout:</span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
            Multimodal: Video + Replay
          </span>
          <span className="px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-[10px] text-amber-400 font-mono">
            Long Context: Full match
          </span>
        </div>
      </motion.div>
    </div>
  );
}

// === ROADMAP SLIDE ===

function RoadmapSlide({
  content,
  slide,
}: {
  content: ExtractContent<"roadmap">;
  slide: Slide;
}) {
  const getNodeColor = (status: "done" | "next" | "future") => {
    if (status === "done") return "bg-green-500";
    if (status === "next") return "bg-amber-500";
    return "bg-zinc-600";
  };

  const getTextColor = (status: "done" | "next" | "future") => {
    if (status === "done") return "text-green-400";
    if (status === "next") return "text-amber-400";
    return "text-zinc-400";
  };

  const getDescColor = (status: "done" | "next" | "future") => {
    if (status === "done") return "text-green-400/70";
    if (status === "next") return "text-amber-400/70";
    return "text-zinc-500";
  };

  // Variant 4: Horizontal Timeline with nodes
  if (content.variant === 4) {
    return (
      <div className="max-w-6xl w-full">
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-6xl font-bold text-white text-center mb-4 font-mono"
        >
          Roadmap
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-amber-400 text-center mb-16"
        >
          {slide.subtitle}
        </motion.p>

        {/* Horizontal timeline */}
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute top-8 left-0 right-0 h-1 bg-zinc-700" />
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: "40%" }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="absolute top-8 left-0 h-1 bg-gradient-to-r from-green-500 to-amber-500"
          />

          {/* Nodes */}
          <div className="flex justify-between relative">
            {content.items.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex flex-col items-center w-1/5"
              >
                {/* Node circle */}
                <div
                  className={`w-16 h-16 rounded-full ${getNodeColor(item.status)} flex items-center justify-center border-4 border-zinc-950 z-10`}
                  style={{ boxShadow: item.status !== "future" ? "0 0 20px rgba(245, 158, 11, 0.3)" : "none" }}
                >
                  <span className="text-zinc-900 font-bold text-lg">{i + 1}</span>
                </div>
                {/* Label */}
                <h3 className={`mt-4 text-lg font-bold text-center ${getTextColor(item.status)}`}>
                  {item.label}
                </h3>
                <p className={`mt-1 text-center text-base ${getDescColor(item.status)} whitespace-pre-line`}>
                  {item.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Variant 5: Vertical flowing timeline
  if (content.variant === 5) {
    return (
      <div className="max-w-4xl w-full">
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-6xl font-bold text-white text-center mb-4 font-mono"
        >
          Roadmap
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-amber-400 text-center mb-12"
        >
          {slide.subtitle}
        </motion.p>

        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-zinc-700" />
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "40%" }}
            transition={{ delay: 0.5, duration: 0.8 }}
            className="absolute left-8 top-0 w-0.5 bg-gradient-to-b from-green-500 to-amber-500"
          />

          <div className="space-y-6">
            {content.items.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="flex items-start gap-6"
              >
                {/* Node */}
                <div
                  className={`w-16 h-16 rounded-full ${getNodeColor(item.status)} flex items-center justify-center flex-shrink-0 z-10`}
                  style={{ boxShadow: item.status !== "future" ? "0 0 15px rgba(245, 158, 11, 0.3)" : "none" }}
                >
                  <span className="text-zinc-900 font-bold text-lg">{i + 1}</span>
                </div>
                {/* Content */}
                <div className="flex-1 pt-3">
                  <h3 className={`text-xl font-bold ${getTextColor(item.status)}`}>
                    {item.label}
                  </h3>
                  <p className={`mt-1 text-base ${getDescColor(item.status)}`}>
                    {item.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Variant 6: Arrow flow (horizontal with connecting arrows)
  if (content.variant === 6) {
    return (
      <div className="max-w-6xl w-full">
        <motion.h2
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-6xl font-bold text-white text-center mb-4 font-mono"
        >
          Roadmap
        </motion.h2>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-amber-400 text-center mb-16"
        >
          {slide.subtitle}
        </motion.p>

        <div className="flex items-center justify-center gap-2">
          {content.items.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 + i * 0.1 }}
              className="flex items-center"
            >
              {/* Arrow-shaped card */}
              <div
                className={`relative px-6 py-4 ${
                  item.status === "done"
                    ? "bg-green-500"
                    : item.status === "next"
                      ? "bg-amber-500"
                      : "bg-zinc-700"
                }`}
                style={{
                  clipPath: "polygon(0 0, calc(100% - 15px) 0, 100% 50%, calc(100% - 15px) 100%, 0 100%, 15px 50%)",
                  marginLeft: i === 0 ? 0 : -10,
                }}
              >
                <h3 className="text-base font-bold text-zinc-900 whitespace-nowrap">
                  {item.label}
                </h3>
                <p className="text-xs text-zinc-800 mt-0.5">
                  {item.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  // Default: simple list (for old variants 1-3)
  return (
    <div className="max-w-4xl w-full">
      <motion.h2
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-6xl font-bold text-white text-center mb-4 font-mono"
      >
        Roadmap
      </motion.h2>
      {slide.subtitle && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-amber-400 text-center mb-12"
        >
          {slide.subtitle}
        </motion.p>
      )}

      <div className="space-y-4">
        {content.items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 + i * 0.08 }}
            className={`p-5 rounded-xl ${
              item.status === "done"
                ? "bg-green-500/20 border border-green-500/50"
                : item.status === "next"
                  ? "bg-amber-500/20 border border-amber-500/50"
                  : "bg-zinc-800/50 border border-zinc-700"
            }`}
          >
            <div className="flex items-start gap-4">
              <div className={`w-4 h-4 rounded-full mt-1 ${getNodeColor(item.status)}`} />
              <div>
                <span className={`text-xl font-medium ${getTextColor(item.status)}`}>
                  {item.label}
                </span>
                <p className={`text-base mt-1 ${getDescColor(item.status)}`}>
                  {item.description}
                </p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

// === CLOSING SLIDE ===

function ClosingSlide({ content }: { content: ExtractContent<"closing"> }) {
  return (
    <div className="text-center max-w-4xl">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: "spring", duration: 0.6 }}
        className="mb-8"
      >
        <ForgingBrand size="xl" />
      </motion.div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-2xl md:text-3xl text-white mb-12"
      >
        {content.tagline}
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="inline-block px-8 py-4 rounded-xl border border-amber-500/50 bg-amber-500/10"
        style={{ boxShadow: "0 0 30px rgba(245, 158, 11, 0.2)" }}
      >
        <span className="text-amber-400 font-mono">{content.badge}</span>
      </motion.div>
    </div>
  );
}
