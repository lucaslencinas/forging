"use client";

import Image from "next/image";

type GameType = "aoe2" | "cs2" | null;

interface GameSelectorPortalProps {
  selectedGame: GameType;
  onSelect: (game: GameType) => void;
}

const games = [
  {
    id: "aoe2" as const,
    name: "Age of Empires II",
    description: "Real-time Strategy",
    image: "/game-placeholders/aoe2.png",
    accentColor: "amber",
  },
  {
    id: "cs2" as const,
    name: "Counter-Strike 2",
    description: "Tactical Shooter",
    image: "/game-placeholders/cs2.png",
    accentColor: "orange",
  },
];

export function GameSelectorPortal({ selectedGame, onSelect }: GameSelectorPortalProps) {
  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        {games.map((game) => {
          const isSelected = selectedGame === game.id;
          const isOtherSelected = selectedGame !== null && !isSelected;

          return (
            <button
              key={game.id}
              onClick={() => onSelect(game.id)}
              className={`
                group relative w-full aspect-[4/3] rounded-2xl overflow-hidden transition-all duration-500 ease-out
                border
                ${isSelected
                  ? "scale-100 opacity-100 border-amber-500/50 ring-1 ring-amber-500/30 shadow-lg shadow-amber-500/10"
                  : isOtherSelected
                    ? "scale-95 opacity-40 blur-sm hover:opacity-100 hover:blur-0 hover:scale-100 border-white/10"
                    : "hover:scale-[1.02] opacity-100 border-white/10 hover:border-white/20"
                }
              `}
            >
              {/* Game Cover Image */}
              <div className="absolute inset-0">
                <Image
                  src={game.image}
                  alt={game.name}
                  fill
                  className="object-cover object-top"
                  sizes="(max-width: 640px) 100vw, 50vw"
                />
                {/* Dark gradient overlay for text readability - stronger at bottom */}
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-transparent" />
              </div>

              {/* Content */}
              <div className="relative z-10 h-full flex flex-col items-center justify-end p-6 text-center">
                {/* Text with background pill for better readability */}
                <div className="bg-black/40 backdrop-blur-sm rounded-xl px-4 py-3 mb-3">
                  <h3 className="text-xl font-semibold text-white mb-0.5">{game.name}</h3>
                  <p className="text-white/70 text-sm">
                    {game.description}
                  </p>
                </div>

                {/* Selection Indicator - amber/gold style matching the theme */}
                <div
                  className={`
                    w-7 h-7 rounded-full border-2 flex items-center justify-center
                    transition-all duration-300
                    ${isSelected
                      ? "bg-amber-500 border-amber-500"
                      : "border-white/30 bg-transparent group-hover:border-white/50"
                    }
                  `}
                >
                  {isSelected && (
                    <svg className="w-4 h-4 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
