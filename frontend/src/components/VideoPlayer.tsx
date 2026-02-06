"use client";

import { useRef, useEffect, useImperativeHandle, forwardRef, useState, useCallback } from "react";
import { VideoControls } from "./VideoControls";

export interface VideoPlayerRef {
  seek: (seconds: number) => void;
  getCurrentTime: () => number;
}

interface VideoPlayerProps {
  src: string;
  onTimeUpdate?: (currentTime: number) => void;
  className?: string;
  voiceEnabled?: boolean;
  onVoiceToggle?: () => void;
}

export const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  function VideoPlayer({ src, onTimeUpdate, className = "", voiceEnabled, onVoiceToggle }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const hideControlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [showControls, setShowControls] = useState(true);

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

    // Auto-hide controls after 3 seconds of no activity
    const resetHideControlsTimeout = useCallback(() => {
      if (hideControlsTimeoutRef.current) {
        clearTimeout(hideControlsTimeoutRef.current);
      }
      setShowControls(true);
      hideControlsTimeoutRef.current = setTimeout(() => {
        if (isPlaying) {
          setShowControls(false);
        }
      }, 3000);
    }, [isPlaying]);

    const handleMouseMove = useCallback(() => {
      resetHideControlsTimeout();
    }, [resetHideControlsTimeout]);

    const handleMouseLeave = useCallback(() => {
      if (isPlaying) {
        setShowControls(false);
      }
    }, [isPlaying]);

    // Control handlers
    const handlePlayPause = useCallback(() => {
      const video = videoRef.current;
      if (!video) return;

      if (video.paused) {
        video.play().catch(() => {});
      } else {
        video.pause();
      }
    }, []);

    const handleSeek = useCallback((time: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = time;
      }
    }, []);

    const handleVolumeChange = useCallback((newVolume: number) => {
      if (videoRef.current) {
        videoRef.current.volume = newVolume;
        setVolume(newVolume);
        if (newVolume > 0 && isMuted) {
          videoRef.current.muted = false;
          setIsMuted(false);
        }
      }
    }, [isMuted]);

    const handleMuteToggle = useCallback(() => {
      if (videoRef.current) {
        videoRef.current.muted = !videoRef.current.muted;
        setIsMuted(!isMuted);
      }
    }, [isMuted]);

    const handleFullscreenToggle = useCallback(() => {
      const container = containerRef.current;
      if (!container) return;

      if (!document.fullscreenElement) {
        container.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }, []);

    // Click on video to play/pause
    const handleVideoClick = useCallback(() => {
      handlePlayPause();
      resetHideControlsTimeout();
    }, [handlePlayPause, resetHideControlsTimeout]);

    useEffect(() => {
      const video = videoRef.current;
      if (!video) return;

      const handleTimeUpdate = () => {
        setCurrentTime(video.currentTime);
        onTimeUpdate?.(video.currentTime);
      };

      const handleLoadedMetadata = () => {
        setDuration(video.duration);
      };

      const handleLoadedData = () => {
        setIsLoading(false);
        setError(null);
      };

      const handleError = () => {
        setIsLoading(false);
        setError("Failed to load video");
      };

      const handlePlay = () => {
        setIsPlaying(true);
      };

      const handlePause = () => {
        setIsPlaying(false);
        setShowControls(true);
      };

      const handleVolumeChangeEvent = () => {
        setVolume(video.volume);
        setIsMuted(video.muted);
      };

      video.addEventListener("timeupdate", handleTimeUpdate);
      video.addEventListener("loadedmetadata", handleLoadedMetadata);
      video.addEventListener("loadeddata", handleLoadedData);
      video.addEventListener("error", handleError);
      video.addEventListener("play", handlePlay);
      video.addEventListener("pause", handlePause);
      video.addEventListener("volumechange", handleVolumeChangeEvent);

      return () => {
        video.removeEventListener("timeupdate", handleTimeUpdate);
        video.removeEventListener("loadedmetadata", handleLoadedMetadata);
        video.removeEventListener("loadeddata", handleLoadedData);
        video.removeEventListener("error", handleError);
        video.removeEventListener("play", handlePlay);
        video.removeEventListener("pause", handlePause);
        video.removeEventListener("volumechange", handleVolumeChangeEvent);
      };
    }, [onTimeUpdate]);

    // Listen for fullscreen changes
    useEffect(() => {
      const handleFullscreenChange = () => {
        setIsFullscreen(!!document.fullscreenElement);
      };

      document.addEventListener("fullscreenchange", handleFullscreenChange);
      return () => {
        document.removeEventListener("fullscreenchange", handleFullscreenChange);
      };
    }, []);

    // Cleanup timeout on unmount
    useEffect(() => {
      return () => {
        if (hideControlsTimeoutRef.current) {
          clearTimeout(hideControlsTimeoutRef.current);
        }
      };
    }, []);

    return (
      <div
        ref={containerRef}
        className={`relative overflow-hidden rounded-xl bg-black ${className}`}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
            <div className="flex flex-col items-center gap-2">
              <svg
                className="h-8 w-8 animate-spin text-amber-500"
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
              <span className="text-2xl">X</span>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        <video
          ref={videoRef}
          src={src}
          className="h-full w-full cursor-pointer"
          playsInline
          onClick={handleVideoClick}
        >
          Your browser does not support the video tag.
        </video>

        <VideoControls
          videoRef={videoRef}
          isPlaying={isPlaying}
          currentTime={currentTime}
          duration={duration}
          volume={volume}
          isMuted={isMuted}
          isFullscreen={isFullscreen}
          showControls={showControls}
          onPlayPause={handlePlayPause}
          onSeek={handleSeek}
          onVolumeChange={handleVolumeChange}
          onMuteToggle={handleMuteToggle}
          onFullscreenToggle={handleFullscreenToggle}
          voiceEnabled={voiceEnabled}
          onVoiceToggle={onVoiceToggle}
        />
      </div>
    );
  }
);
