"use client";

import { useRef, useState, useEffect, ReactNode } from "react";

interface HorizontalCarouselProps {
  children: ReactNode;
  className?: string;
  showArrows?: boolean;
  showDots?: boolean;
}

export function HorizontalCarousel({
  children,
  className = "",
  showArrows = true,
  showDots = true,
}: HorizontalCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  const updateScrollState = () => {
    const container = scrollRef.current;
    if (!container) return;

    const { scrollLeft, scrollWidth, clientWidth } = container;
    setCanScrollLeft(scrollLeft > 0);
    setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 1);

    // Calculate scroll progress (0 to 1)
    const maxScroll = scrollWidth - clientWidth;
    setScrollProgress(maxScroll > 0 ? scrollLeft / maxScroll : 0);
  };

  useEffect(() => {
    updateScrollState();
    const container = scrollRef.current;
    if (container) {
      container.addEventListener("scroll", updateScrollState);
      window.addEventListener("resize", updateScrollState);
      return () => {
        container.removeEventListener("scroll", updateScrollState);
        window.removeEventListener("resize", updateScrollState);
      };
    }
  }, [children]);

  const scroll = (direction: "left" | "right") => {
    const container = scrollRef.current;
    if (!container) return;

    const scrollAmount = container.clientWidth * 0.8;
    container.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  return (
    <div className={`relative group ${className}`}>
      {/* Left arrow */}
      {showArrows && canScrollLeft && (
        <button
          onClick={() => scroll("left")}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-zinc-800/90 hover:bg-zinc-700 border border-zinc-700 rounded-full p-2 shadow-lg transition-all opacity-0 group-hover:opacity-100 -translate-x-1/2"
          aria-label="Scroll left"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}

      {/* Scrollable container */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto scrollbar-hide scroll-smooth pb-2"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {children}
      </div>

      {/* Right arrow */}
      {showArrows && canScrollRight && (
        <button
          onClick={() => scroll("right")}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-zinc-800/90 hover:bg-zinc-700 border border-zinc-700 rounded-full p-2 shadow-lg transition-all opacity-0 group-hover:opacity-100 translate-x-1/2"
          aria-label="Scroll right"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Scroll progress indicator */}
      {showDots && (canScrollLeft || canScrollRight) && (
        <div className="mt-4 flex justify-center">
          <div className="h-1 w-24 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-orange-500 rounded-full transition-all duration-300"
              style={{ width: `${Math.max(20, (1 - scrollProgress) * 100)}%`, marginLeft: `${scrollProgress * 80}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
