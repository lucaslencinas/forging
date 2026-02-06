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
  },
  {
    id: "cs2" as const,
    name: "Counter-Strike 2",
    subtitle: "Demo Files",
    icon: "🎯",
    fileType: ".dem",
  },
];

export function GameSelector({ selectedGame, onSelect }: GameSelectorProps) {
  return (
    <div className="space-y-6">
      <h3 className="text-center text-xl font-semibold text-white">
        Select your game
      </h3>
      <div className="grid gap-6 sm:grid-cols-2">
        {games.map((game) => {
          const isSelected = selectedGame === game.id;
          return (
            <button
              key={game.id}
              onClick={() => onSelect(isSelected ? null : game.id)}
              className={`
                relative overflow-hidden rounded-3xl border p-8 text-left transition-all duration-300
                ${isSelected
                  ? "border-amber-500 bg-white/10 shadow-lg shadow-amber-500/20"
                  : "border-white/10 bg-white/5 hover:bg-white/[0.07] hover:border-white/20"
                }
              `}
            >
              <div className="flex items-start gap-4">
                <span className="text-5xl">{game.icon}</span>
                <div className="flex-1">
                  <h4 className="text-2xl font-semibold text-white mb-1">{game.name}</h4>
                  <p className="text-sm text-zinc-400 mb-3">{game.subtitle}</p>
                  <p className="text-xs text-zinc-600 font-mono">
                    File type: {game.fileType}
                  </p>
                </div>
              </div>
              {isSelected && (
                <div className="absolute right-6 top-6">
                  <div className="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center">
                    <svg
                      className="h-5 w-5 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
