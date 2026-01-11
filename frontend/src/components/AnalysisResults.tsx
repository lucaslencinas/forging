"use client";

import type { components } from "@/types/api";

type AnalysisResponse = components["schemas"]["AnalysisResponse"];
type Player = components["schemas"]["Player"];

interface AnalysisResultsProps {
  result: AnalysisResponse;
  onReset: () => void;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export function AnalysisResults({
  result,
  onReset,
  onReanalyze,
  isReanalyzing,
}: AnalysisResultsProps) {
  const { game_type, game_summary, analysis } = result;

  const gameLabel =
    game_type === "aoe2" ? "Age of Empires II" : "Counter-Strike 2";
  const gameIcon = game_type === "aoe2" ? "🏰" : "🎯";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-4xl">{gameIcon}</span>
          <div>
            <h2 className="text-2xl font-bold">{gameLabel} Analysis</h2>
            <p className="text-zinc-400">
              {analysis.provider && analysis.model_used
                ? `via ${analysis.provider} (${analysis.model_used})`
                : "AI-powered coaching feedback"}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          {onReanalyze && (
            <button
              onClick={onReanalyze}
              disabled={isReanalyzing}
              className="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium transition-colors hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isReanalyzing ? (
                <span className="flex items-center gap-2">
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                "Analyze Again"
              )}
            </button>
          )}
          <button
            onClick={onReset}
            className="rounded-lg border border-zinc-700 px-4 py-2 text-sm font-medium transition-colors hover:bg-zinc-800"
          >
            Analyze Another Game
          </button>
        </div>
      </div>

      {/* Game Summary */}
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/50 p-6">
        <h3 className="mb-4 text-lg font-semibold text-zinc-300">
          Game Summary
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg bg-zinc-900/50 p-4">
            <p className="text-sm text-zinc-500">Map</p>
            <p className="text-lg font-medium">{game_summary.map}</p>
          </div>
          <div className="rounded-lg bg-zinc-900/50 p-4">
            <p className="text-sm text-zinc-500">Map Size</p>
            <p className="text-lg font-medium">{game_summary.map_size}</p>
          </div>
          <div className="rounded-lg bg-zinc-900/50 p-4">
            <p className="text-sm text-zinc-500">Duration</p>
            <p className="text-lg font-medium">{game_summary.duration}</p>
          </div>
          <div className="rounded-lg bg-zinc-900/50 p-4">
            <p className="text-sm text-zinc-500">Rated</p>
            <p className="text-lg font-medium">
              {game_summary.rated ? "Yes" : "No"}
            </p>
          </div>
        </div>

        {/* Players */}
        <div className="mt-6">
          <h4 className="mb-3 text-sm font-medium text-zinc-400">Players</h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {game_summary.players.map((player: Player, i: number) => (
              <div
                key={i}
                className={`rounded-lg p-4 ${
                  player.winner
                    ? "bg-green-900/30 border border-green-700"
                    : "bg-zinc-900/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{player.name}</span>
                  {player.winner && (
                    <span className="text-xs font-medium text-green-400">
                      WINNER
                    </span>
                  )}
                </div>
                <p className="text-sm text-zinc-400">
                  {player.civilization} • Rating: {player.rating || "Unranked"}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error State */}
      {analysis.error && (
        <div className="rounded-xl border border-red-500/50 bg-red-500/10 p-6">
          <h3 className="font-semibold text-red-400">Analysis Error</h3>
          <p className="mt-2 text-zinc-400">{analysis.error}</p>
        </div>
      )}

      {/* Tips */}
      {analysis.tips && analysis.tips.length > 0 && (
        <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-6">
          <h3 className="mb-4 text-lg font-semibold text-orange-400">
            Tips to Improve
          </h3>
          <ul className="space-y-4">
            {analysis.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-4">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-orange-500/20 text-sm font-bold text-orange-400">
                  {i + 1}
                </span>
                <span className="text-zinc-300 leading-relaxed">{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
