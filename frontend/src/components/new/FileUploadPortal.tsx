"use client";

import { useState, useCallback, useEffect } from "react";
import { useVideoUpload } from "@/hooks/useVideoUpload";
import { PlayerSelector } from "@/components/PlayerSelector";

type GameType = "aoe2" | "cs2";

interface DemoPlayer {
  name: string;
  team: string | null;
}

interface ReplayPlayer {
  name: string;
  civilization: string | null;
  color: string | null;
}

interface FileUploadPortalProps {
  gameType: GameType;
  onVideoAnalyze: (videoObjectName: string, replayFile: File | null, povPlayer: string | null) => void;
  isLoading: boolean;
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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export function FileUploadPortal({ gameType, onVideoAnalyze, isLoading }: FileUploadPortalProps) {
  const [replayFile, setReplayFile] = useState<File | null>(null);
  const [replayObjectName, setReplayObjectName] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isHovering, setIsHovering] = useState(false);
  const videoUpload = useVideoUpload();

  // Player selection state
  const [players, setPlayers] = useState<(DemoPlayer | ReplayPlayer)[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [isParsingReplay, setIsParsingReplay] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const config = gameConfig[gameType];

  // Upload replay and parse for players when both files are ready
  useEffect(() => {
    const uploadAndParse = async () => {
      if (!replayFile || videoUpload.status !== "complete") {
        return;
      }

      // Skip if already uploaded this file
      if (replayObjectName) {
        return;
      }

      setIsParsingReplay(true);
      setParseError(null);

      try {
        // Step 1: Upload replay file to GCS
        const uploadUrlResponse = await fetch(`${API_URL}/api/replay/upload-url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: replayFile.name,
            content_type: "application/octet-stream",
            file_size: replayFile.size,
          }),
        });

        if (!uploadUrlResponse.ok) {
          throw new Error("Failed to get replay upload URL");
        }

        const { signed_url, object_name } = await uploadUrlResponse.json();

        // Upload to GCS
        const uploadResponse = await fetch(signed_url, {
          method: "PUT",
          headers: { "Content-Type": "application/octet-stream" },
          body: replayFile,
        });

        if (!uploadResponse.ok) {
          throw new Error("Failed to upload replay file");
        }

        setReplayObjectName(object_name);

        // Step 2: Parse for players (different endpoint based on game type)
        const parseEndpoint = gameType === "cs2"
          ? `${API_URL}/api/demo/parse-players`
          : `${API_URL}/api/replay/parse-players`;

        const parseBody = gameType === "cs2"
          ? { demo_object_name: object_name }
          : { replay_object_name: object_name };

        const parseResponse = await fetch(parseEndpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(parseBody),
        });

        if (!parseResponse.ok) {
          throw new Error(`Failed to parse ${gameType === "cs2" ? "demo" : "replay"} file`);
        }

        const data = await parseResponse.json();
        setPlayers(data.players);
      } catch (err) {
        setParseError(err instanceof Error ? err.message : "Failed to parse replay");
      } finally {
        setIsParsingReplay(false);
      }
    };

    uploadAndParse();
  }, [gameType, replayFile, videoUpload.status, replayObjectName]);

  // Reset player state when replay file changes
  useEffect(() => {
    setPlayers([]);
    setSelectedPlayer(null);
    setReplayObjectName(null);
    setParseError(null);
  }, [replayFile]);

  // Handle Drag & Drop
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsHovering(true);
    } else if (e.type === "dragleave") {
      setIsHovering(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsHovering(false);

      const files = e.dataTransfer.files;
      if (files?.[0]) {
        const file = files[0];
        const extension = file.name.split(".").pop()?.toLowerCase();

        if (extension === "aoe2record" || extension === "dem") {
          setReplayFile(file);
        } else if (extension === "mp4" || extension === "webm") {
          setVideoFile(file);
          videoUpload.upload(file);
        }
      }
    },
    [videoUpload]
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
      await videoUpload.upload(file);
    }
  };

  const handleRemoveReplay = () => {
    setReplayFile(null);
    setReplayObjectName(null);
    setPlayers([]);
    setSelectedPlayer(null);
  };

  const handleRemoveVideo = () => {
    setVideoFile(null);
    videoUpload.reset();
  };

  const handleAnalyze = () => {
    if (videoUpload.objectName && replayFile) {
      onVideoAnalyze(videoUpload.objectName, replayFile, selectedPlayer);
    }
  };

  const isVideoUploading = videoUpload.status === "uploading" || videoUpload.status === "validating";
  const isVideoReady = videoUpload.status === "complete";
  const isPlayerSelected = selectedPlayer !== null;
  const showPlayerSelector = isVideoReady && replayFile && (players.length > 0 || isParsingReplay);
  const canAnalyze = isVideoReady && videoUpload.objectName && replayFile && isPlayerSelected && !isLoading && !isParsingReplay;

  return (
    <div className="w-full max-w-3xl mx-auto mt-8 animate-in fade-in slide-in-from-bottom-8 duration-500">
      <div
        className={`
          relative rounded-xl border overflow-hidden transition-all duration-300
          ${isHovering ? "border-white/40 bg-white/10" : "border-white/10 bg-black/40"}
          backdrop-blur-xl
        `}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <div className="p-4 space-y-3">
          {/* Replay Upload Row */}
          <div
            className={`
              relative rounded-lg border-2 border-dashed px-3 py-2.5 transition-all
              ${replayFile
                ? "border-amber-500/40 bg-amber-500/5"
                : "border-zinc-700 bg-zinc-800/30 hover:border-zinc-600"
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
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-amber-400 font-medium text-sm truncate max-w-[280px]">{replayFile.name}</span>
                  <span className="text-xs text-zinc-500">
                    ({(replayFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  onClick={(e) => { e.preventDefault(); handleRemoveReplay(); }}
                  className="text-zinc-400 hover:text-red-400 p-1 transition-colors"
                  title="Remove file"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="text-center py-1.5">
                <p className="text-zinc-300 text-sm">{config.description}</p>
                <p className="text-xs text-zinc-500">or click to browse</p>
              </div>
            )}
          </div>

          {/* Video Upload Row */}
          <div
            className={`
              relative rounded-lg border-2 border-dashed px-3 py-2.5 transition-all
              ${videoFile
                ? "border-amber-500/40 bg-amber-500/5"
                : "border-zinc-700 bg-zinc-800/30 hover:border-zinc-600"
              }
              ${isVideoUploading ? "pointer-events-none" : ""}
            `}
          >
            <input
              type="file"
              accept=".mp4"
              onChange={handleVideoChange}
              className="absolute inset-0 cursor-pointer opacity-0"
              disabled={isVideoUploading}
            />

            {videoFile ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {isVideoReady ? (
                      <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : isVideoUploading ? (
                      <svg className="w-4 h-4 text-amber-400 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : null}
                    <span className={`${isVideoReady ? "text-amber-400" : "text-zinc-300"} font-medium text-sm truncate max-w-[280px]`}>{videoFile.name}</span>
                    <span className="text-xs text-zinc-500">
                      ({(videoFile.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  <button
                    onClick={(e) => { e.preventDefault(); handleRemoveVideo(); }}
                    disabled={isVideoUploading}
                    className="text-zinc-400 hover:text-red-400 disabled:opacity-50 disabled:cursor-not-allowed p-1 transition-colors"
                    title="Remove file"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>

                {/* Progress bar */}
                {isVideoUploading && (
                  <div className="w-full bg-zinc-700 rounded-full h-1.5">
                    <div
                      className="bg-amber-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${videoUpload.progress}%` }}
                    />
                  </div>
                )}

                {/* Status message - only show for errors or during upload */}
                {videoUpload.status === "validating" && (
                  <p className="text-xs text-zinc-500">Validating video...</p>
                )}
                {videoUpload.status === "uploading" && (
                  <p className="text-xs text-zinc-500">Uploading: {videoUpload.progress}%</p>
                )}
                {videoUpload.error && (
                  <p className="text-xs text-red-400">{videoUpload.error}</p>
                )}
              </div>
            ) : (
              <div className="text-center py-1.5">
                <p className="text-zinc-300 text-sm">Drop your video file here</p>
                <p className="text-xs text-zinc-500">or click to browse (MP4, max 700MB)</p>
              </div>
            )}
          </div>

          {/* Player Selector */}
          {showPlayerSelector && (
            <PlayerSelector
              players={players}
              selectedPlayer={selectedPlayer}
              onSelect={setSelectedPlayer}
              isLoading={isParsingReplay}
              gameType={gameType}
            />
          )}

          {/* Parse error */}
          {parseError && (
            <p className="text-center text-sm text-red-400">{parseError}</p>
          )}

          {/* Hints */}
          {videoFile && !replayFile && (
            <p className="text-center text-xs text-amber-500">
              Replay file required for analysis
            </p>
          )}

          {isVideoReady && replayFile && !selectedPlayer && !isParsingReplay && players.length > 0 && (
            <p className="text-center text-xs text-amber-500">
              Select your player above to continue
            </p>
          )}

          {/* Analyze Button - smaller, centered, matching home CTA style */}
          <div className="flex justify-center pt-2">
            <button
              onClick={handleAnalyze}
              disabled={!canAnalyze}
              className={`
                px-8 py-3 rounded-lg font-semibold text-sm transition-all duration-300
                ${canAnalyze
                  ? "bg-amber-500 text-black hover:bg-amber-400 shadow-lg shadow-amber-500/20"
                  : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                }
              `}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Analyze Gameplay
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
