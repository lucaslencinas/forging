"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  followUpQuestions?: string[];
}

interface ChatSidebarProps {
  analysisId: string;
  gameType: string;
  onWidthChange?: (width: number) => void;
}

// Pre-made question chips by game type
const QUESTION_CHIPS: Record<string, string[]> = {
  cs2: [
    "What should I buy first round?",
    "How was my crosshair placement?",
    "When should I rotate?",
  ],
  aoe2: [
    "What counters the enemy's army?",
    "Was my build order efficient?",
    "When should I have attacked?",
  ],
};

const MIN_WIDTH = 280;
const MAX_WIDTH = 600;
const DEFAULT_WIDTH = 384; // 96 * 4 = w-96

export function ChatSidebar({ analysisId, gameType, onWidthChange }: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interactionId, setInteractionId] = useState<string | null>(null);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [usedChips, setUsedChips] = useState<Set<string>>(new Set());
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isDragging, setIsDragging] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Get chips for this game type, fallback to cs2
  const allChips = QUESTION_CHIPS[gameType] || QUESTION_CHIPS.cs2;
  // Filter out used chips
  const availableChips = allChips.filter((chip) => !usedChips.has(chip));

  // Get follow-up questions from the last assistant message
  const lastMessage = messages[messages.length - 1];
  const followUpQuestions = lastMessage?.role === "assistant" ? lastMessage.followUpQuestions : undefined;

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
      setWidth(clampedWidth);
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

  const sendMessage = async (messageText?: string) => {
    const userMessage = (messageText || input).trim();
    if (!userMessage || isLoading) return;

    setInput("");
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
        `${process.env.NEXT_PUBLIC_API_URL}/api/analysis/${analysisId}/chat`,
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
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: data.response,
        followUpQuestions: data.follow_up_questions,
      }]);
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

  // Mobile toggle button
  const MobileToggle = () => (
    <button
      onClick={() => setIsMobileOpen(!isMobileOpen)}
      className="fixed bottom-4 right-4 z-50 lg:hidden bg-amber-500 hover:bg-amber-600 text-white rounded-full p-4 shadow-lg transition-all"
      title="Ask the AI Coach"
    >
      {isMobileOpen ? (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ) : (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
      )}
    </button>
  );

  const ChatContent = () => (
    <div className="flex flex-col h-full bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-950 border-l border-white/10">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/[0.02] backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          <span className="text-sm font-semibold text-white">AI Coach</span>
          <span className="text-xs text-zinc-500 uppercase font-medium">({gameType})</span>
        </div>
        {/* Mobile close button */}
        <button
          onClick={() => setIsMobileOpen(false)}
          className="lg:hidden text-zinc-400 hover:text-white transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 flex items-center justify-center">
              <svg className="w-8 h-8 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <p className="text-white text-sm font-medium mb-2">Ask questions about your gameplay!</p>
            <p className="text-zinc-500 text-xs">Try clicking one of the suggestions below</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm transition-all ${ msg.role === "user"
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
                <div className="h-2 w-2 animate-bounce rounded-full bg-amber-400" style={{ animationDelay: "0ms" }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-amber-400" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-amber-400" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-500/10 border-t border-red-500/30 text-red-400 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Question chips - show remaining chips or follow-up questions */}
      {(availableChips.length > 0 || (followUpQuestions && followUpQuestions.length > 0)) && !isLoading && (
        <div className="px-4 pb-3">
          <div className="flex flex-wrap gap-2">
            {/* Show follow-up questions from the LLM first */}
            {followUpQuestions?.map((question, i) => (
              <button
                key={`follow-${i}`}
                onClick={() => handleChipClick(question)}
                disabled={isLoading}
                className="px-3 py-2 text-xs rounded-full font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:border-amber-500/50 hover:bg-amber-500/20 hover:shadow-lg hover:shadow-amber-500/10 transition-all disabled:opacity-50"
              >
                {question}
              </button>
            ))}
            {/* Show remaining preset chips */}
            {availableChips.map((chip, i) => (
              <button
                key={`chip-${i}`}
                onClick={() => handleChipClick(chip)}
                disabled={isLoading}
                className="px-3 py-2 text-xs rounded-full font-medium bg-white/5 text-zinc-300 border border-white/10 hover:border-amber-500/50 hover:text-amber-400 hover:bg-white/[0.07] transition-all disabled:opacity-50"
              >
                {chip}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-white/10 bg-white/[0.02]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20 transition-all backdrop-blur-sm"
            disabled={isLoading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading}
            className="bg-gradient-to-br from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 disabled:from-zinc-700 disabled:to-zinc-800 disabled:cursor-not-allowed text-white rounded-xl px-4 py-3 text-sm font-medium transition-all shadow-lg shadow-amber-500/20 disabled:shadow-none"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar - always visible with draggable divider */}
      <div
        ref={sidebarRef}
        className="hidden lg:block h-full fixed right-0 top-0 pt-[73px]"
        style={{ width: `${width}px` }}
      >
        {/* Draggable divider */}
        <div
          onMouseDown={handleMouseDown}
          className={`absolute left-0 top-0 bottom-0 w-1 cursor-ew-resize group z-10 ${
            isDragging ? "bg-amber-500" : "bg-transparent hover:bg-amber-500/50"
          }`}
        >
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-16 rounded-full bg-zinc-600 group-hover:bg-amber-400 transition-colors" />
        </div>
        <ChatContent />
      </div>

      {/* Drag overlay to prevent text selection while dragging */}
      {isDragging && <div className="fixed inset-0 z-50 cursor-ew-resize" />}

      {/* Mobile toggle button */}
      <MobileToggle />

      {/* Mobile full-screen overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setIsMobileOpen(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-md">
            <ChatContent />
          </div>
        </div>
      )}
    </>
  );
}
