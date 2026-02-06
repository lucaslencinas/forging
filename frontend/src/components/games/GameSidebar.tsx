"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import type { components } from "@/types/api";

type TimestampedTip = components["schemas"]["TimestampedTip"];

interface Message {
  role: "user" | "assistant";
  content: string;
  followUpQuestions?: string[];
}

interface GameSidebarProps {
  analysisId: string;
  gameType: string;
  tips: TimestampedTip[];
  currentTime: number;
  onSeek: (seconds: number) => void;
  onWidthChange?: (width: number) => void;
  isAnalyzing?: boolean;
}

const MIN_WIDTH = 280;
const MAX_WIDTH = 600;
const DEFAULT_WIDTH = 384;

// Pre-made question chips by game type - 4 questions each, shown progressively
const QUESTION_CHIPS: Record<string, string[]> = {
  cs2: [
    "What should I buy first round?",
    "How was my crosshair placement?",
    "When should I rotate?",
    "How can I improve my utility usage?",
  ],
  aoe2: [
    "What counters the enemy's army?",
    "Was my build order efficient?",
    "When should I have attacked?",
    "How many villagers should I have on each resource?",
  ],
};

// Re-using the formatTime helper
const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export function GameSidebar({
  analysisId,
  gameType,
  tips,
  currentTime,
  onSeek,
  onWidthChange,
  isAnalyzing = false,
}: GameSidebarProps) {
  const [activeTab, setActiveTab] = useState<"aicoach" | "insights">("insights");
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interactionId, setInteractionId] = useState<string | null>(null);
  const [usedChips, setUsedChips] = useState<Set<string>>(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle drag resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = window.innerWidth - e.clientX;
      const clampedWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, newWidth));
      onWidthChange?.(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, onWidthChange]);

  // Get chips for this game type, fallback to cs2
  const allChips = QUESTION_CHIPS[gameType] || QUESTION_CHIPS.cs2;
  // Filter out used chips
  const availableChips = allChips.filter((chip) => !usedChips.has(chip));

  // Get follow-up questions from the last assistant message
  const lastMessage = messages[messages.length - 1];
  const followUpQuestions =
    lastMessage?.role === "assistant" ? lastMessage.followUpQuestions : undefined;

  // Always show exactly 2 suggestions total
  // Priority: follow-up questions first, then fill with preset chips
  const followUpsToShow = followUpQuestions?.slice(0, 2) || [];
  const remainingSlots = 2 - followUpsToShow.length;
  const chipsToShow = remainingSlots > 0 ? availableChips.slice(0, remainingSlots) : [];

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (messageText?: string) => {
    const userMessage = (messageText || chatInput).trim();
    if (!userMessage || isLoading) return;

    setChatInput("");
    setError(null);

    // Track used chips
    if (allChips.includes(userMessage)) {
      setUsedChips((prev) => new Set([...prev, userMessage]));
    }

    // Add user message to chat
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}/api/analysis/${analysisId}/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage,
            previous_interaction_id: interactionId,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Chat failed: ${response.statusText}`);
      }

      const data = await response.json();

      // Add assistant response with follow-up questions if available
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          followUpQuestions: data.follow_up_questions,
        },
      ]);
      setInteractionId(data.interaction_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleChipClick = (question: string) => {
    sendMessage(question);
  };

  return (
    <>
    <div className="h-full flex flex-col bg-black/20 backdrop-blur-md border-l border-white/10 relative">
      {/* Draggable resize handle - only show when onWidthChange is provided (desktop mode) */}
      {onWidthChange && (
        <div
          onMouseDown={handleMouseDown}
          className={`absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize group z-10 ${
            isDragging ? "bg-amber-500" : "bg-transparent hover:bg-amber-500/50"
          }`}
        >
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-16 rounded-full bg-zinc-600 group-hover:bg-amber-400 transition-colors" />
        </div>
      )}

      {/* Tabs Header */}
      <div className="flex border-b border-white/10">
        <button
          onClick={() => setActiveTab("aicoach")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            activeTab === "aicoach"
              ? "bg-white/10 text-white border-b-2 border-amber-500"
              : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
          }`}
        >
          AI Coach
        </button>
        <button
          onClick={() => setActiveTab("insights")}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            activeTab === "insights"
              ? "bg-white/10 text-white border-b-2 border-amber-500"
              : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
          }`}
        >
          Tips
          <span className="ml-2 px-1.5 py-0.5 rounded-full bg-white/10 text-xs">
            {tips?.length || 0}
          </span>
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {/* VIEW: AI COACH (Chat) */}
        {activeTab === "aicoach" && (
          <div className="h-full flex flex-col">

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar">
              {/* Show waiting message when analyzing */}
              {isAnalyzing && messages.length === 0 && (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 flex items-center justify-center">
                    <div className="w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <p className="text-amber-400 text-sm font-medium mb-2">
                    Analysis in progress...
                  </p>
                  <p className="text-zinc-500 text-xs">
                    AI Coach will be available once analysis completes
                  </p>
                </div>
              )}
              {!isAnalyzing && messages.length === 0 && (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 flex items-center justify-center">
                    <svg
                      className="w-8 h-8 text-amber-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                      />
                    </svg>
                  </div>
                  <p className="text-white text-sm font-medium mb-2">
                    Ask questions about your gameplay!
                  </p>
                  <p className="text-zinc-500 text-xs">
                    Try clicking one of the suggestions below
                  </p>
                </div>
              )}

              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm transition-all ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white shadow-lg shadow-amber-500/20"
                        : "bg-white/5 text-zinc-200 border border-white/10 backdrop-blur-sm"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm prose-invert max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5 prose-strong:text-amber-300 prose-code:bg-white/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-white/5 text-zinc-400 rounded-2xl px-4 py-3 text-sm border border-white/10 backdrop-blur-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-2 w-2 animate-bounce rounded-full bg-amber-400"
                        style={{ animationDelay: "0ms" }}
                      />
                      <div
                        className="h-2 w-2 animate-bounce rounded-full bg-amber-400"
                        style={{ animationDelay: "150ms" }}
                      />
                      <div
                        className="h-2 w-2 animate-bounce rounded-full bg-amber-400"
                        style={{ animationDelay: "300ms" }}
                      />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Error */}
            {error && (
              <div className="px-6 py-2 bg-red-500/10 border-t border-red-500/30 text-red-400 text-xs font-medium">
                {error}
              </div>
            )}

            {/* Question chips - always show exactly 2 suggestions */}
            {!isAnalyzing &&
              (followUpsToShow.length > 0 || chipsToShow.length > 0) &&
              !isLoading && (
                <div className="px-6 pb-3">
                  <div className="flex flex-wrap gap-2">
                    {/* Show follow-up questions from the LLM first */}
                    {followUpsToShow.map((question, i) => (
                      <button
                        key={`follow-${i}`}
                        onClick={() => handleChipClick(question)}
                        disabled={isLoading}
                        className="px-3 py-2 text-xs rounded-full font-medium bg-white/5 text-zinc-300 border border-white/20 hover:border-white/40 hover:bg-white/10 hover:text-white transition-all disabled:opacity-50"
                      >
                        {question}
                      </button>
                    ))}
                    {/* Fill remaining slots with preset chips */}
                    {chipsToShow.map((chip, i) => (
                      <button
                        key={`chip-${i}`}
                        onClick={() => handleChipClick(chip)}
                        disabled={isLoading}
                        className="px-3 py-2 text-xs rounded-full font-medium bg-white/5 text-zinc-300 border border-white/20 hover:border-white/40 hover:bg-white/10 hover:text-white transition-all disabled:opacity-50"
                      >
                        {chip}
                      </button>
                    ))}
                  </div>
                </div>
              )}

            {/* Input */}
            <div className="p-4 border-t border-white/10 bg-white/[0.02]">
              <div className="relative group">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isAnalyzing ? "Available after analysis completes..." : "Ask a question..."}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20 transition-colors font-mono placeholder:text-zinc-600 disabled:opacity-50"
                  disabled={isLoading || isAnalyzing}
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={!chatInput.trim() || isLoading || isAnalyzing}
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-gradient-to-br from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 disabled:from-zinc-700 disabled:to-zinc-800 disabled:cursor-not-allowed text-white rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* VIEW: INSIGHTS (Tips) */}
        {activeTab === "insights" && (
          <div className="absolute inset-0 overflow-y-auto p-4 custom-scrollbar space-y-3">
            {/* Skeleton loading state while analyzing */}
            {isAnalyzing && (!tips || tips.length === 0) && (
              <>
                <div className="text-center py-4 text-amber-400 text-sm font-medium animate-pulse">
                  Tips will appear as the AI analyzes your gameplay...
                </div>
                {[1, 2, 3].map((i) => (
                  <div
                    key={`skeleton-${i}`}
                    className="rounded-lg border bg-white/5 border-white/5 p-3 animate-pulse"
                  >
                    <div className="flex gap-2 mb-2">
                      <div className="h-4 w-12 bg-white/10 rounded" />
                      <div className="h-4 w-16 bg-white/10 rounded" />
                    </div>
                    <div className="space-y-2">
                      <div className="h-3 bg-white/10 rounded w-full" />
                      <div className="h-3 bg-white/10 rounded w-3/4" />
                    </div>
                  </div>
                ))}
              </>
            )}
            {tips?.map((tip, idx) => {
              // Find the next tip's timestamp (or Infinity if this is the last tip)
              const nextTipTime = tips[idx + 1]?.timestamp_seconds ?? Infinity;
              // A tip is "active/highlighted" when currentTime is between this tip and the next tip
              const isHighlighted = currentTime >= tip.timestamp_seconds && currentTime < nextTipTime;

              // Use a stable key based on content
              const tipKey = `tip-${tip.timestamp_seconds}-${idx}`;

              const handleTipClick = (e: React.MouseEvent) => {
                e.stopPropagation();
                onSeek(tip.timestamp_seconds);
              };

              return (
                <div
                  key={tipKey}
                  onClick={handleTipClick}
                  className={`
                    group cursor-pointer rounded-lg border p-3 transition-all duration-300
                    ${
                      isHighlighted
                        ? "bg-amber-500/10 border-amber-500/50 shadow-[0_0_15px_rgba(249,115,22,0.1)]"
                        : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/20"
                    }
                  `}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-mono text-xs px-1.5 py-0.5 rounded ${isHighlighted ? "bg-amber-500 text-black" : "bg-white/10 text-zinc-400"}`}
                      >
                        {tip.timestamp_display || formatTime(tip.timestamp_seconds)}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-zinc-500 border border-white/5 px-1.5 rounded">
                        {tip.category}
                      </span>
                    </div>
                    {tip.confidence && tip.confidence > 8 && (
                      <span className="text-[10px] text-green-500 font-mono">
                        HIGH CONFIDENCE
                      </span>
                    )}
                  </div>
                  <p
                    className={`text-sm leading-relaxed ${isHighlighted ? "text-white" : "text-zinc-400 group-hover:text-zinc-300"}`}
                  >
                    {tip.tip}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>

    {/* Drag overlay to prevent text selection while dragging */}
    {isDragging && <div className="fixed inset-0 z-50 cursor-ew-resize" />}
    </>
  );
}
