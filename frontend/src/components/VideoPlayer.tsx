"use client";

import { useRef, useEffect, useImperativeHandle, forwardRef, useState } from "react";

export interface VideoPlayerRef {
  seek: (seconds: number) => void;
  getCurrentTime: () => number;
}

interface VideoPlayerProps {
  src: string;
  onTimeUpdate?: (currentTime: number) => void;
  className?: string;
}

export const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  function VideoPlayer({ src, onTimeUpdate, className = "" }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useImperativeHandle(ref, () => ({
      seek: (seconds: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = seconds;
          videoRef.current.play().catch(() => {
            // Autoplay might be blocked, that's ok
          });
        }
      },
      getCurrentTime: () => {
        return videoRef.current?.currentTime ?? 0;
      },
    }));

    useEffect(() => {
      const video = videoRef.current;
      if (!video) return;

      const handleTimeUpdate = () => {
        onTimeUpdate?.(video.currentTime);
      };

      const handleLoadedData = () => {
        setIsLoading(false);
        setError(null);
      };

      const handleError = () => {
        setIsLoading(false);
        setError("Failed to load video");
      };

      video.addEventListener("timeupdate", handleTimeUpdate);
      video.addEventListener("loadeddata", handleLoadedData);
      video.addEventListener("error", handleError);

      return () => {
        video.removeEventListener("timeupdate", handleTimeUpdate);
        video.removeEventListener("loadeddata", handleLoadedData);
        video.removeEventListener("error", handleError);
      };
    }, [onTimeUpdate]);

    return (
      <div className={`relative overflow-hidden rounded-xl bg-black ${className}`}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
            <div className="flex flex-col items-center gap-2">
              <svg
                className="h-8 w-8 animate-spin text-orange-500"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <span className="text-sm text-zinc-400">Loading video...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
            <div className="flex flex-col items-center gap-2 text-red-400">
              <span className="text-2xl">❌</span>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        <video
          ref={videoRef}
          src={src}
          controls
          className="h-full w-full"
          playsInline
        >
          Your browser does not support the video tag.
        </video>
      </div>
    );
  }
);
