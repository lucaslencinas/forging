export function Footer() {
  return (
    <footer className="border-t border-zinc-800 px-6 py-12">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-orange-500">Forging</span>
            <span className="text-sm text-zinc-500">AI Game Coach</span>
          </div>

          <div className="flex items-center gap-6 text-sm text-zinc-400">
            <a
              href="https://github.com/lucaslencinas/forging"
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-white"
            >
              GitHub
            </a>
            <span className="text-zinc-600">|</span>
            <span>Built for the Gemini 3 Hackathon</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
