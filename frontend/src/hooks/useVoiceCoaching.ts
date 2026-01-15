"use client";

import { useRef, useEffect, useState, useCallback } from "react";

interface Tip {
  timestamp_seconds: number;
  tip: string;
}

/**
 * Hook to manage voice coaching - plays audio clips in sync with video playback.
 *
 * @param tips - Array of tips with timestamps
 * @param audioUrls - Array of signed URLs for audio files (same order as tips)
 * @param currentTime - Current video playback time in seconds
 * @param enabled - Whether voice coaching is enabled
 */
export function useVoiceCoaching(
  tips: Tip[],
  audioUrls: string[],
  currentTime: number,
  enabled: boolean
) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playedTips, setPlayedTips] = useState<Set<number>>(new Set());
  const lastTimeRef = useRef(currentTime);
  const [isPlaying, setIsPlaying] = useState(false);
  const wasEnabledRef = useRef(enabled);

  // Create audio element on mount
  useEffect(() => {
    audioRef.current = new Audio();
    audioRef.current.addEventListener("playing", () => setIsPlaying(true));
    audioRef.current.addEventListener("ended", () => setIsPlaying(false));
    audioRef.current.addEventListener("pause", () => setIsPlaying(false));

    return () => {
      audioRef.current?.pause();
      audioRef.current = null;
    };
  }, []);

  // Reset played tips when seeking backward
  useEffect(() => {
    if (currentTime < lastTimeRef.current - 1) {
      // Seeked backward, reset tips that are after current time
      setPlayedTips((prev) => {
        const newSet = new Set<number>();
        prev.forEach((i) => {
          if (tips[i] && tips[i].timestamp_seconds < currentTime) {
            newSet.add(i);
          }
        });
        return newSet;
      });
    }
    lastTimeRef.current = currentTime;
  }, [currentTime, tips]);

  // Play audio when tip becomes active
  useEffect(() => {
    if (!enabled || audioUrls.length === 0 || !audioRef.current) return;

    // Find tip that just became active
    for (let i = 0; i < tips.length; i++) {
      const tipTime = tips[i].timestamp_seconds;
      const nextTipTime = tips[i + 1]?.timestamp_seconds ?? Infinity;

      // Calculate the trigger window:
      // - Start: tip time (or 0 if tip is at the very beginning)
      // - End: tip time + 3s OR next tip time, whichever is smaller
      const windowStart = tipTime;
      const windowEnd = Math.min(tipTime + 3, nextTipTime);

      // Check if current time is within the trigger window for this tip
      if (currentTime >= windowStart && currentTime < windowEnd) {
        if (!playedTips.has(i) && audioUrls[i]) {
          audioRef.current.src = audioUrls[i];
          audioRef.current.play().catch(() => {
            // Autoplay may be blocked
          });
          setPlayedTips((prev) => new Set([...prev, i]));
          break;
        }
      }
    }
  }, [currentTime, tips, audioUrls, enabled, playedTips]);

  // Handle enable/disable transitions
  useEffect(() => {
    if (!enabled && audioRef.current) {
      // Stop audio when disabled
      audioRef.current.pause();
    }

    // When voice is enabled, reset played tips to allow replaying from current position
    if (enabled && !wasEnabledRef.current) {
      // Just enabled - mark tips before current time as already played
      const newPlayedSet = new Set<number>();
      for (let i = 0; i < tips.length; i++) {
        // Only mark as played if we're well past the tip's window
        if (tips[i].timestamp_seconds < currentTime - 3) {
          newPlayedSet.add(i);
        }
      }
      setPlayedTips(newPlayedSet);
    }

    wasEnabledRef.current = enabled;
  }, [enabled, tips, currentTime]);

  const stop = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const reset = useCallback(() => {
    setPlayedTips(new Set());
  }, []);

  return { stop, reset, isPlaying };
}
