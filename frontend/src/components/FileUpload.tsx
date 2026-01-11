"use client";

import { useState, useCallback } from "react";
import { useVideoUpload } from "@/hooks/useVideoUpload";

type GameType = "aoe2" | "cs2";

interface FileUploadProps {
  gameType: GameType;
  onAnalyze: (replayFile: File, videoObjectName?: string) => void;
  isLoading: boolean;
  loadingState: string;
}

const gameConfig = {
  aoe2: {
    accept: ".aoe2record",
    label: "AoE2 Replay",
    description: "Drop your .aoe2record file here",
  },
  cs2: {
    accept: ".dem",
    label: "CS2 Demo",
    description: "Drop your .dem file here",
  },
};

export function FileUpload({
  gameType,
  onAnalyze,
  isLoading,
  loadingState,
}: FileUploadProps) {
  const [replayFile, setReplayFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const videoUpload = useVideoUpload();

  const config = gameConfig[gameType];

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = e.dataTransfer.files;
      if (files?.[0]) {
        const file = files[0];
        const extension = file.name.split(".").pop()?.toLowerCase();

        if (extension === "aoe2record" || extension === "dem") {
          setReplayFile(file);
        } else if (extension === "mp4" || extension === "webm") {
          setVideoFile(file);
        }
      }
    },
    []
  );

  const handleReplayChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setReplayFile(file);
    }
  };

  const handleVideoChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      // Start upload immediately
      await videoUpload.upload(file);
    }
  };

  const handleRemoveVideo = () => {
    setVideoFile(null);
    videoUpload.reset();
  };

  const handleSubmit = () => {
    if (replayFile) {
      // Pass the uploaded video object name if available
      onAnalyze(replayFile, videoUpload.objectName || undefined);
    }
  };

  const isVideoUploading = videoUpload.status === "uploading" || videoUpload.status === "validating";
  const isVideoReady = videoUpload.status === "complete";
  const canSubmit = replayFile && !isLoading && !isVideoUploading;

  return (
    <div className="space-y-6">
      {/* Replay File Upload */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${dragActive
            ? "border-orange-500 bg-orange-500/10"
            : replayFile
              ? "border-green-500 bg-green-500/10"
              : "border-zinc-700 bg-zinc-800/50 hover:border-zinc-600"
          }
        `}
      >
        <input
          type="file"
          accept={config.accept}
          onChange={handleReplayChange}
          className="absolute inset-0 cursor-pointer opacity-0"
        />

        {replayFile ? (
          <div className="space-y-2">
            <div className="text-4xl">✅</div>
            <p className="font-medium text-green-400">{replayFile.name}</p>
            <p className="text-sm text-zinc-500">
              {(replayFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl">📁</div>
            <p className="font-medium text-zinc-300">{config.description}</p>
            <p className="text-sm text-zinc-500">or click to browse</p>
          </div>
        )}
      </div>

      {/* Video File Upload (Optional) */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/30 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-zinc-300">
              Video Recording (Optional)
            </h4>
            <p className="text-sm text-zinc-500">
              Add a screen recording for enhanced AI analysis (MP4, max 500MB, 15 min)
            </p>
          </div>
          <label className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
            isVideoUploading
              ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              : "bg-zinc-700 cursor-pointer hover:bg-zinc-600"
          }`}>
            {isVideoUploading ? "Uploading..." : videoFile ? "Change" : "Add Video"}
            <input
              type="file"
              accept=".mp4"
              onChange={handleVideoChange}
              className="hidden"
              disabled={isVideoUploading}
            />
          </label>
        </div>

        {/* Video upload progress */}
        {videoFile && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <span>{isVideoReady ? "✅" : isVideoUploading ? "⏳" : videoUpload.status === "error" ? "❌" : "🎥"}</span>
              <span className={isVideoReady ? "text-green-400" : ""}>{videoFile.name}</span>
              <span className="text-zinc-600">
                ({(videoFile.size / 1024 / 1024).toFixed(2)} MB)
              </span>
              <button
                onClick={handleRemoveVideo}
                disabled={isVideoUploading}
                className="ml-auto text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Remove
              </button>
            </div>

            {/* Progress bar */}
            {isVideoUploading && (
              <div className="w-full bg-zinc-700 rounded-full h-2">
                <div
                  className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${videoUpload.progress}%` }}
                />
              </div>
            )}

            {/* Status message */}
            {videoUpload.status === "validating" && (
              <p className="text-xs text-zinc-500">Validating video...</p>
            )}
            {videoUpload.status === "uploading" && (
              <p className="text-xs text-zinc-500">Uploading: {videoUpload.progress}%</p>
            )}
            {isVideoReady && (
              <p className="text-xs text-green-500">Video uploaded successfully</p>
            )}
            {videoUpload.error && (
              <p className="text-xs text-red-400">{videoUpload.error}</p>
            )}
          </div>
        )}
      </div>

      {/* Analyze Button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className={`
          w-full rounded-xl py-4 text-lg font-semibold transition-all
          ${canSubmit
            ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white hover:from-orange-600 hover:to-amber-600"
            : "cursor-not-allowed bg-zinc-700 text-zinc-500"
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg
              className="h-5 w-5 animate-spin"
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
            {loadingState === "uploading" ? "Uploading..." : "Analyzing with AI..."}
          </span>
        ) : (
          "Analyze Game"
        )}
      </button>
    </div>
  );
}
