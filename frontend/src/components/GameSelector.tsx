"use client";

type GameType = "aoe2" | "cs2" | null;

interface GameSelectorProps {
  selectedGame: GameType;
  onSelect: (game: GameType) => void;
}

const games = [
  {
    id: "aoe2" as const,
    name: "Age of Empires II",
    subtitle: "Definitive Edition",
    icon: "🏰",
    fileType: ".aoe2record",
    color: "from-amber-600 to-amber-800",
    borderColor: "border-amber-500",
  },
  {
    id: "cs2" as const,
    name: "Counter-Strike 2",
    subtitle: "Demo Files",
    icon: "🎯",
    fileType: ".dem",
    color: "from-blue-600 to-blue-800",
    borderColor: "border-blue-500",
  },
];

export function GameSelector({ selectedGame, onSelect }: GameSelectorProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-center text-lg font-medium text-zinc-300">
        Select your game
      </h3>
      <div className="grid gap-4 sm:grid-cols-2">
        {games.map((game) => {
          const isSelected = selectedGame === game.id;
          return (
            <button
              key={game.id}
              onClick={() => onSelect(isSelected ? null : game.id)}
              className={`
                relative overflow-hidden rounded-xl border-2 p-6 text-left transition-all
                ${isSelected
                  ? `${game.borderColor} bg-gradient-to-br ${game.color}`
                  : "border-zinc-700 bg-zinc-800/50 hover:border-zinc-600 hover:bg-zinc-800"
                }
              `}
            >
              <div className="flex items-start gap-4">
                <span className="text-4xl">{game.icon}</span>
                <div>
                  <h4 className="text-xl font-semibold">{game.name}</h4>
                  <p className="text-sm text-zinc-400">{game.subtitle}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    File type: {game.fileType}
                  </p>
                </div>
              </div>
              {isSelected && (
                <div className="absolute right-4 top-4">
                  <svg
                    className="h-6 w-6 text-white"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
