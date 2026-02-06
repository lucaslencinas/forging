"use client";

type GameType = "aoe2" | "cs2";

interface Player {
  name: string;
  team?: string | null;
  civilization?: string | null;
  color?: string | null;
}

interface PlayerSelectorProps {
  players: Player[];
  selectedPlayer: string | null;
  onSelect: (playerName: string) => void;
  isLoading?: boolean;
  gameType: GameType;
}

export function PlayerSelector({
  players,
  selectedPlayer,
  onSelect,
  isLoading = false,
  gameType,
}: PlayerSelectorProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/30 p-4">
        <div className="flex items-center gap-3">
          <svg
            className="h-5 w-5 animate-spin text-amber-500"
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
          <span className="text-zinc-400">
            Parsing {gameType === "cs2" ? "demo" : "replay"} file...
          </span>
        </div>
      </div>
    );
  }

  // CS2: Group players by team
  if (gameType === "cs2") {
    const teamT = players.filter((p) => p.team === "T" || p.team === "TERRORIST");
    const teamCT = players.filter((p) => p.team === "CT" || p.team === "COUNTER_TERRORIST");
    const unknown = players.filter((p) => !p.team || (p.team !== "T" && p.team !== "CT" && p.team !== "TERRORIST" && p.team !== "COUNTER_TERRORIST"));

    const renderPlayerButton = (player: Player) => {
      const isSelected = selectedPlayer === player.name;
      return (
        <button
          key={player.name}
          onClick={() => onSelect(player.name)}
          className={`
            rounded-lg px-3 py-2 text-left transition-all text-sm
            ${
              isSelected
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
                : "bg-zinc-800 hover:bg-zinc-700 border border-transparent"
            }
          `}
        >
          <span className="font-medium">{player.name}</span>
        </button>
      );
    };

    return (
      <div className="rounded-xl border border-zinc-700 bg-zinc-800/30 p-4 space-y-3">
        <div>
          <h4 className="font-medium text-zinc-300 text-sm">Select Your Username</h4>
          <p className="text-xs text-zinc-500">
            Choose which player is you in the demo for personalized tips
          </p>
        </div>

        {/* Team T */}
        {teamT.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-amber-500">T Side</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {teamT.map(renderPlayerButton)}
            </div>
          </div>
        )}

        {/* Team CT */}
        {teamCT.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-zinc-300">CT Side</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {teamCT.map(renderPlayerButton)}
            </div>
          </div>
        )}

        {/* Unknown team */}
        {unknown.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase text-zinc-400">Players</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {unknown.map(renderPlayerButton)}
            </div>
          </div>
        )}

        {selectedPlayer && (
          <p className="text-sm text-amber-400">
            Tips will be personalized for: <span className="font-medium">{selectedPlayer}</span>
          </p>
        )}
      </div>
    );
  }

  // AoE2: Show players with civilization
  const renderAoE2PlayerButton = (player: Player) => {
    const isSelected = selectedPlayer === player.name;
    return (
      <button
        key={player.name}
        onClick={() => onSelect(player.name)}
        className={`
          rounded-lg px-3 py-2 text-left transition-all text-sm
          ${
            isSelected
              ? "bg-amber-500/20 text-amber-300 border border-amber-500/50"
              : "bg-zinc-800 hover:bg-zinc-700 border border-transparent"
          }
        `}
      >
        <span className="font-medium">{player.name}</span>
        {player.civilization && (
          <span className={`ml-2 text-sm ${isSelected ? "text-amber-100" : "text-zinc-400"}`}>
            ({player.civilization})
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="rounded-xl border border-zinc-700 bg-zinc-800/30 p-4 space-y-3">
      <div>
        <h4 className="font-medium text-zinc-300 text-sm">Select Your Player</h4>
        <p className="text-xs text-zinc-500">
          Choose which player is you in the replay for personalized tips
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {players.map(renderAoE2PlayerButton)}
      </div>

      {selectedPlayer && (
        <p className="text-sm text-amber-400">
          Tips will be personalized for: <span className="font-medium">{selectedPlayer}</span>
        </p>
      )}
    </div>
  );
}
