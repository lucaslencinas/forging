"use client";

import { CS2AnalysisView } from "./CS2AnalysisView";
import { AoE2AnalysisView } from "./AoE2AnalysisView";
import type { components } from "@/types/api";

type GameSummary = components["schemas"]["GameSummary"];
type CS2Content = components["schemas"]["CS2Content"];
type AoE2Content = components["schemas"]["AoE2Content"];

// Define analysis type that can come from different sources
interface AnalysisData {
  game_type?: string;
  tips?: components["schemas"]["TimestampedTip"][];
  game_summary?: GameSummary | null;
  model_used?: string;
  provider?: string;
  share_url?: string;
  error?: string | null;
  cs2_content?: CS2Content | null;
  aoe2_content?: AoE2Content | null;
}

interface VideoAnalysisResultsProps {
  analysis: AnalysisData;
  videoUrl: string;
  audioUrls?: string[];
}

/**
 * VideoAnalysisResults - Routes to game-specific analysis views.
 *
 * This component acts as a router, delegating to the appropriate
 * game-specific view based on game_type. This avoids conditional
 * logic scattered throughout the component tree.
 */
export function VideoAnalysisResults({ analysis, videoUrl, audioUrls = [] }: VideoAnalysisResultsProps) {
  const tips = analysis.tips || [];

  // Route to CS2-specific view
  if (analysis.game_type === "cs2") {
    return (
      <CS2AnalysisView
        tips={tips}
        gameSummary={analysis.game_summary}
        roundsTimeline={analysis.cs2_content?.rounds_timeline || []}
        videoUrl={videoUrl}
        audioUrls={audioUrls}
        modelUsed={analysis.model_used}
        provider={analysis.provider}
        shareUrl={analysis.share_url}
        error={analysis.error}
      />
    );
  }

  // Default to AoE2 view (also handles unknown game types)
  return (
    <AoE2AnalysisView
      tips={tips}
      gameSummary={analysis.game_summary}
      aoe2Content={analysis.aoe2_content}
      videoUrl={videoUrl}
      audioUrls={audioUrls}
      modelUsed={analysis.model_used}
      provider={analysis.provider}
      shareUrl={analysis.share_url}
      error={analysis.error}
    />
  );
}
