"use client";

import { useEffect, useState, useCallback } from "react";
import { AnimatePresence } from "motion/react";
import { slides } from "./slides-data";
import { SlideProgress } from "./SlideProgress";
import { NeonForgeSlides } from "./versions/NeonForgeSlides";

export function SlideViewer() {
  const [currentSlide, setCurrentSlide] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const totalSlides = slides.length;

  const goToSlide = useCallback(
    (slideNumber: number) => {
      if (slideNumber >= 1 && slideNumber <= totalSlides) {
        setCurrentSlide(slideNumber);
      }
    },
    [totalSlides]
  );

  const nextSlide = useCallback(() => {
    goToSlide(currentSlide + 1);
  }, [currentSlide, goToSlide]);

  const prevSlide = useCallback(() => {
    goToSlide(currentSlide - 1);
  }, [currentSlide, goToSlide]);

  const toggleFullscreen = useCallback(async () => {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      await document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent default for navigation keys
      if (
        ["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "Space", "Home", "End"].includes(
          e.code
        )
      ) {
        e.preventDefault();
      }

      switch (e.code) {
        case "ArrowRight":
        case "ArrowDown":
        case "Space":
          nextSlide();
          break;
        case "ArrowLeft":
        case "ArrowUp":
          prevSlide();
          break;
        case "Home":
          goToSlide(1);
          break;
        case "End":
          goToSlide(totalSlides);
          break;
        case "KeyF":
          toggleFullscreen();
          break;
        case "KeyN":
          setShowNotes((prev) => !prev);
          break;
        case "Escape":
          if (document.fullscreenElement) {
            document.exitFullscreen();
            setIsFullscreen(false);
          }
          break;
        case "Slash":
          if (e.shiftKey) {
            setShowHelp((prev) => !prev);
          }
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [nextSlide, prevSlide, goToSlide, totalSlides, toggleFullscreen]);

  // Handle fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  const slide = slides[currentSlide - 1];

  return (
    <div className="relative w-full h-screen bg-zinc-950 overflow-hidden">
      {/* Slide content */}
      <AnimatePresence mode="wait">
        <NeonForgeSlides slide={slide} />
      </AnimatePresence>

      {/* Progress bar */}
      <SlideProgress current={currentSlide} total={totalSlides} variant="glow" />

      {/* Presenter notes */}
      {showNotes && slide.notes && (
        <div className="fixed bottom-16 left-4 right-4 z-50 p-4 bg-zinc-900/95 backdrop-blur-sm rounded-lg border border-zinc-800 text-zinc-400 text-sm">
          <span className="text-zinc-500 text-xs uppercase tracking-wide mb-2 block">
            Notes
          </span>
          {slide.notes}
        </div>
      )}

      {/* Keyboard help overlay */}
      {showHelp && (
        <div className="fixed inset-0 z-50 bg-zinc-950/90 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-zinc-900 rounded-2xl border border-zinc-800 p-8 max-w-md">
            <h3 className="text-xl font-bold text-white mb-6">Keyboard Shortcuts</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-zinc-400">Next slide</span>
                <span className="text-zinc-500 font-mono">→ ↓ Space</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Previous slide</span>
                <span className="text-zinc-500 font-mono">← ↑</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">First / Last</span>
                <span className="text-zinc-500 font-mono">Home / End</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Fullscreen</span>
                <span className="text-zinc-500 font-mono">F</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">Toggle notes</span>
                <span className="text-zinc-500 font-mono">N</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-400">This help</span>
                <span className="text-zinc-500 font-mono">?</span>
              </div>
            </div>
            <button
              onClick={() => setShowHelp(false)}
              className="mt-6 w-full py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Navigation hint - only shown briefly on first load, non-fullscreen */}
      {!isFullscreen && (
        <div className="fixed bottom-4 left-4 text-zinc-600 text-sm">
          Press <span className="text-zinc-500 font-mono">?</span> for keyboard shortcuts
        </div>
      )}

      {/* Click areas for navigation */}
      <div
        className="fixed left-0 top-0 bottom-0 w-1/4 cursor-pointer z-40"
        onClick={prevSlide}
      />
      <div
        className="fixed right-0 top-0 bottom-0 w-1/4 cursor-pointer z-40"
        onClick={nextSlide}
      />
    </div>
  );
}
