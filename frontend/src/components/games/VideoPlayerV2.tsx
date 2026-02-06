"use client";

import {
  useRef,
  useState,
  forwardRef,
  useImperativeHandle,
  SyntheticEvent,
} from "react";

interface VideoPlayerV2Props {
  videoUrl: string;
  posterUrl?: string;
  onProgress?: (seconds: number) => void;
}

export interface VideoPlayerV2Ref {
  seek: (seconds: number) => void;
}

export const VideoPlayerV2 = forwardRef<VideoPlayerV2Ref, VideoPlayerV2Props>(
  ({ videoUrl, posterUrl, onProgress }, ref) => {
    const [playing, setPlaying] = useState(false);
    const [progressPct, setProgressPct] = useState(0);
    const [duration, setDuration] = useState(0);
    const videoRef = useRef<HTMLVideoElement>(null);

    useImperativeHandle(ref, () => ({
      seek: (seconds: number) => {
        if (videoRef.current) {
          videoRef.current.currentTime = seconds;
        }
      },
    }));

    const handleTimeUpdate = (e: SyntheticEvent<HTMLVideoElement>) => {
      const video = e.currentTarget;
      if (video.duration) {
        const pct = (video.currentTime / video.duration) * 100;
        setProgressPct(pct);
        if (onProgress) onProgress(video.currentTime);
      }
    };

    const handleDurationChange = (e: SyntheticEvent<HTMLVideoElement>) => {
      const video = e.currentTarget;
      if (video.duration && isFinite(video.duration)) {
        setDuration(video.duration);
      }
    };

    const handlePlay = () => {
      if (videoRef.current) {
        if (playing) {
          videoRef.current.pause();
        } else {
          videoRef.current.play();
        }
        setPlaying(!playing);
      }
    };

    const handleProgressBarClick = (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
      if (videoRef.current && duration > 0) {
        const rect = e.currentTarget.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const seekTime = percentage * duration;
        videoRef.current.currentTime = seekTime;
      }
    };

    const formatTime = (seconds: number) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    return (
      <div className="w-full h-full bg-black relative z-10 overflow-hidden group/player">
        {/* Native Video Player - responsive without cropping */}
        <video
          ref={videoRef}
          src={videoUrl}
          poster={posterUrl}
          className="w-full h-full object-contain cursor-pointer"
          crossOrigin="anonymous"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleDurationChange}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
          onClick={handlePlay}
        />

        {/* Floating Controls Overlay - minimal on mobile */}
        <div
          className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover/player:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-2 sm:p-4 md:p-6 pointer-events-none"
        >
          {/* Progress Bar */}
          <div
            className="w-full h-1 bg-white/20 rounded-full mb-2 sm:mb-3 cursor-pointer group/progress relative pointer-events-auto"
            onClick={handleProgressBarClick}
          >
            <div
              className="h-full bg-amber-500 rounded-full relative"
              style={{ width: `${progressPct}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-white rounded-full scale-0 group-hover/progress:scale-100 transition-transform shadow-lg" />
            </div>
          </div>

          {/* Controls Row - minimal on mobile */}
          <div className="flex items-center gap-2 sm:gap-3 pointer-events-auto">
            <button
              onClick={handlePlay}
              className="w-7 h-7 sm:w-9 sm:h-9 md:w-10 md:h-10 rounded-full bg-white text-black flex items-center justify-center hover:scale-110 transition-transform flex-shrink-0"
            >
              {playing ? (
                <svg className="w-3 h-3 sm:w-4 sm:h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M5 4h5v16H5V4zm9 0h5v16h-5V4z" />
                </svg>
              ) : (
                <svg className="w-3 h-3 sm:w-4 sm:h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </button>
            <div className="font-mono text-[10px] sm:text-xs text-white/80">
              {formatTime((progressPct / 100) * duration)} / {formatTime(duration)}
            </div>
          </div>
        </div>
      </div>
    );
  }
);

VideoPlayerV2.displayName = "VideoPlayerV2";
