"use client";

import { useState } from "react";
import { slides } from "@/components/slides/slides-data";

type Section = "preDemo" | "demo" | "postDemo";

// Define which slides belong to each section
const DEMO_SLIDE_ID = 8; // The "Let me show you how it works" slide

// Demo actions (these are not slides, so we keep them as static content)
const demoActions = [
  {
    action: "Navigate to Upload",
    script:
      "Upload is simple - select your game, drop your replay action file and video. Select a player and click upload.",
  },
  {
    action: "Show Completed Analysis",
    script:
      "After a few minutes, you will get a full analysis of your gameplay. Notice the coaching tips - each one is timestamped to specific moments in the match.",
  },
  {
    action: "Click Timestamp",
    script:
      "Click any timestamp and you jump directly to that moment. No scrubbing through video trying to find what the coach is talking about.",
  },
  {
    action: "Show Chat",
    script:
      "The real power is the chat. 'Why did I lose that fight?' 'How should I have played that round?' The AI has FULL CONTEXT of your entire match - every moment, every decision. This isn't a generic chatbot - it actually watched your game.",
  },
];

// Estimate duration based on word count (~150 words/min = ~2.5 words/sec)
function estimateDuration(script: string): string {
  const words = script.split(/\s+/).length;
  const seconds = Math.round(words / 2.5);
  return `~${seconds}s`;
}

export default function ScriptPage() {
  const [activeSection, setActiveSection] = useState<Section>("preDemo");

  // Split slides into pre-demo and post-demo based on the demo transition slide
  const preDemoSlides = slides.filter((s) => s.id < DEMO_SLIDE_ID && s.script);
  const postDemoSlides = slides.filter((s) => s.id > DEMO_SLIDE_ID && s.script);

  const sections: { id: Section; label: string; color: string }[] = [
    { id: "preDemo", label: "Pre-Demo (Slides)", color: "amber" },
    { id: "demo", label: "Live Demo", color: "green" },
    { id: "postDemo", label: "Post-Demo (Slides)", color: "blue" },
  ];

  const colorClasses = {
    amber: {
      active: "bg-amber-500 text-zinc-950",
      inactive: "text-amber-400 border-amber-500/30 hover:bg-amber-500/10",
      card: "border-amber-500/30 bg-amber-500/5",
      badge: "bg-amber-500/20 text-amber-400",
    },
    green: {
      active: "bg-green-500 text-zinc-950",
      inactive: "text-green-400 border-green-500/30 hover:bg-green-500/10",
      card: "border-green-500/30 bg-green-500/5",
      badge: "bg-green-500/20 text-green-400",
    },
    blue: {
      active: "bg-blue-500 text-zinc-950",
      inactive: "text-blue-400 border-blue-500/30 hover:bg-blue-500/10",
      card: "border-blue-500/30 bg-blue-500/5",
      badge: "bg-blue-500/20 text-blue-400",
    },
  };

  const currentColor =
    sections.find((s) => s.id === activeSection)?.color || "amber";
  const colors = colorClasses[currentColor as keyof typeof colorClasses];

  // Calculate total times
  const preDemoWords = preDemoSlides.reduce(
    (acc, s) => acc + (s.script?.split(/\s+/).length || 0),
    0
  );
  const postDemoWords = postDemoSlides.reduce(
    (acc, s) => acc + (s.script?.split(/\s+/).length || 0),
    0
  );
  const demoWords = demoActions.reduce(
    (acc, a) => acc + a.script.split(/\s+/).length,
    0
  );

  const preDemoSeconds = Math.round(preDemoWords / 2.5);
  const postDemoSeconds = Math.round(postDemoWords / 2.5);
  const demoSeconds = Math.round(demoWords / 2.5);
  const totalSeconds = preDemoSeconds + postDemoSeconds + demoSeconds;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-zinc-950/95 backdrop-blur-md border-b border-zinc-800 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl font-mono font-bold tracking-tighter text-amber-500">
              FORGING
            </span>
            <span className="text-zinc-500 text-sm">Presenter Script</span>
          </div>
          <a
            href="/slides"
            className="text-zinc-400 hover:text-white text-sm transition-colors"
          >
            ← Back to Slides
          </a>
        </div>
      </header>

      {/* Section Tabs */}
      <div className="sticky top-[65px] z-40 bg-zinc-950/95 backdrop-blur-md border-b border-zinc-800 px-6 py-3">
        <div className="max-w-4xl mx-auto flex gap-3">
          {sections.map((section) => {
            const sectionColors =
              colorClasses[section.color as keyof typeof colorClasses];
            const isActive = activeSection === section.id;
            return (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`px-4 py-2 rounded-lg border font-medium transition-all ${isActive ? sectionColors.active : sectionColors.inactive
                  }`}
              >
                {section.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Section Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            {activeSection === "preDemo" && "Pre-Demo: Setting the Stage"}
            {activeSection === "demo" && "Live Demo: Showing FORGING"}
            {activeSection === "postDemo" && "Post-Demo: Technical & Closing"}
          </h1>
          <p className="text-zinc-400">
            {activeSection === "preDemo" &&
              `Build the narrative before showing the product. ~${formatTime(preDemoSeconds)}`}
            {activeSection === "demo" &&
              `Walk through the actual product. ~${formatTime(demoSeconds)} (speaking only)`}
            {activeSection === "postDemo" &&
              `Technical credibility and closing. ~${formatTime(postDemoSeconds)}`}
          </p>
        </div>

        {/* Script Cards */}
        <div className="space-y-6">
          {activeSection === "preDemo" &&
            preDemoSlides.map((slide, i) => (
              <ScriptCard
                key={slide.id}
                index={i + 1}
                title={slide.title}
                duration={estimateDuration(slide.script || "")}
                script={slide.script || ""}
                colors={colors}
              />
            ))}

          {activeSection === "demo" &&
            demoActions.map((item, i) => (
              <ScriptCard
                key={i}
                index={i + 1}
                title={item.action}
                duration={estimateDuration(item.script)}
                script={item.script}
                colors={colors}
                isAction
              />
            ))}

          {activeSection === "postDemo" &&
            postDemoSlides.map((slide, i) => (
              <ScriptCard
                key={slide.id}
                index={i + 1}
                title={slide.title}
                duration={estimateDuration(slide.script || "")}
                script={slide.script || ""}
                colors={colors}
              />
            ))}
        </div>

        {/* Total Time */}
        <div className="mt-12 p-6 rounded-xl border border-zinc-800 bg-zinc-900/50">
          <h3 className="text-lg font-bold text-white mb-4">
            Total Presentation Time
          </h3>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <span className="text-2xl font-bold text-amber-400">
                ~{formatTime(preDemoSeconds)}
              </span>
              <p className="text-zinc-500 text-sm">Pre-Demo</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-green-400">
                ~{formatTime(demoSeconds)}
              </span>
              <p className="text-zinc-500 text-sm">Live Demo</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-blue-400">
                ~{formatTime(postDemoSeconds)}
              </span>
              <p className="text-zinc-500 text-sm">Post-Demo</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-zinc-800 text-center">
            <span className="text-3xl font-bold text-white">
              ~{formatTime(totalSeconds)} Total
            </span>
          </div>
        </div>

        {/* Tips */}
        <div className="mt-8 p-6 rounded-xl border border-zinc-800 bg-zinc-900/50">
          <h3 className="text-lg font-bold text-white mb-4">
            Presentation Tips
          </h3>
          <ul className="space-y-2 text-zinc-400">
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              Speak slowly and clearly - you have time
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              Have the demo pre-loaded in a browser tab ready to go
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              Use an already-analyzed game for the demo - don&apos;t wait for
              processing
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              Emphasize &quot;full match context&quot; when showing the chat
              feature
            </li>
            <li className="flex items-start gap-2">
              <span className="text-amber-500 mt-1">•</span>
              End with energy - &quot;Built for Gemini&quot; should feel
              confident
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}

function ScriptCard({
  index,
  title,
  duration,
  script,
  colors,
  isAction = false,
}: {
  index: number;
  title: string;
  duration: string;
  script: string;
  colors: {
    card: string;
    badge: string;
  };
  isAction?: boolean;
}) {
  return (
    <div className={`p-6 rounded-xl border ${colors.card}`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-sm font-bold text-zinc-400">
            {index}
          </span>
          <div>
            <span className="text-xs text-zinc-500 uppercase tracking-wide">
              {isAction ? "Action" : "Slide"}
            </span>
            <h3 className="text-lg font-bold text-white">{title}</h3>
          </div>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-mono ${colors.badge}`}
        >
          {duration}
        </span>
      </div>
      <p className="text-zinc-300 leading-relaxed text-lg">
        &ldquo;{script}&rdquo;
      </p>
    </div>
  );
}
