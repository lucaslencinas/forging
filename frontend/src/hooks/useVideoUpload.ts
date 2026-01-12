"use client";

import { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const MAX_FILE_SIZE_MB = 500;
const MAX_DURATION_SECONDS = 900; // 15 minutes

interface VideoUploadState {
  status: "idle" | "validating" | "uploading" | "complete" | "error";
  progress: number;
  error: string | null;
  objectName: string | null;
}

interface UploadUrlResponse {
  signed_url: string;
  object_name: string;
  expiry_minutes: number;
  bucket: string;
}

export function useVideoUpload() {
  const [state, setState] = useState<VideoUploadState>({
    status: "idle",
    progress: 0,
    error: null,
    objectName: null,
  });

  const validateVideo = useCallback(async (file: File): Promise<string | null> => {
    // Check file type
    if (file.type !== "video/mp4") {
      return "Only MP4 files are supported";
    }

    // Check file size
    const maxBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
    if (file.size > maxBytes) {
      return `File too large. Maximum size is ${MAX_FILE_SIZE_MB}MB`;
    }

    // Check duration using video element
    return new Promise((resolve) => {
      const video = document.createElement("video");
      video.preload = "metadata";

      video.onloadedmetadata = () => {
        URL.revokeObjectURL(video.src);
        if (video.duration > MAX_DURATION_SECONDS) {
          resolve(`Video too long. Maximum duration is ${MAX_DURATION_SECONDS / 60} minutes`);
        } else {
          resolve(null);
        }
      };

      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        resolve("Could not read video file");
      };

      video.src = URL.createObjectURL(file);
    });
  }, []);

  const upload = useCallback(async (file: File): Promise<string | null> => {
    setState({
      status: "validating",
      progress: 0,
      error: null,
      objectName: null,
    });

    // Validate the video
    const validationError = await validateVideo(file);
    if (validationError) {
      setState({
        status: "error",
        progress: 0,
        error: validationError,
        objectName: null,
      });
      return null;
    }

    setState((prev) => ({ ...prev, status: "uploading" }));

    try {
      // Get signed URL from backend
      const urlResponse = await fetch(`${API_URL}/api/video/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type,
          file_size: file.size,
        }),
      });

      if (!urlResponse.ok) {
        const error = await urlResponse.json();
        throw new Error(error.detail || "Failed to get upload URL");
      }

      const { signed_url, object_name }: UploadUrlResponse = await urlResponse.json();

      // Upload to GCS with progress tracking
      // Large files (500MB) may take several minutes to upload
      await new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.timeout = 600000; // 10 minute timeout for large files

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setState((prev) => ({ ...prev, progress }));
          }
        };

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        };

        xhr.onerror = () => reject(new Error("Upload failed. Check your connection."));
        xhr.ontimeout = () => reject(new Error("Upload timed out. Try a smaller file or check your connection."));

        xhr.open("PUT", signed_url);
        xhr.setRequestHeader("Content-Type", file.type);
        xhr.send(file);
      });

      setState({
        status: "complete",
        progress: 100,
        error: null,
        objectName: object_name,
      });

      return object_name;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Upload failed";
      setState({
        status: "error",
        progress: 0,
        error: errorMessage,
        objectName: null,
      });
      return null;
    }
  }, [validateVideo]);

  const reset = useCallback(() => {
    setState({
      status: "idle",
      progress: 0,
      error: null,
      objectName: null,
    });
  }, []);

  return {
    ...state,
    upload,
    reset,
  };
}
