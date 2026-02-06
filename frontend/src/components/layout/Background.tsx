/**
 * Shared background component with gradient overlay, diagonal grid pattern,
 * and ambient glow effects. Used across all pages for visual consistency.
 */
export function Background() {
  return (
    <>
      {/* Background gradient overlay */}
      <div className="fixed inset-0 bg-gradient-to-b from-zinc-900 via-zinc-950 to-zinc-950 pointer-events-none" />

      {/* Subtle diagonal grid pattern */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(45deg, rgba(255,255,255,0.2) 1px, transparent 1px),
            linear-gradient(-45deg, rgba(255,255,255,0.2) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Subtle ambient glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {/* Top amber glow */}
        <div className="absolute -top-[30%] left-1/2 -translate-x-1/2 w-[90%] h-[50%] bg-amber-500/[0.07] rounded-full blur-3xl" />
        {/* Middle accent */}
        <div className="absolute top-[40%] -left-[10%] w-[40%] h-[30%] bg-orange-500/[0.04] rounded-full blur-3xl" />
        {/* Bottom purple glow */}
        <div className="absolute -bottom-[10%] right-0 w-[60%] h-[40%] bg-purple-500/[0.05] rounded-full blur-3xl" />
      </div>
    </>
  );
}
