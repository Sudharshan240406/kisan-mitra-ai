export function BackgroundFX() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* Ambient gradient orbs */}
      <div className="absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full bg-[var(--forest-800)] opacity-20 blur-[120px]" />
      <div className="absolute -bottom-40 -right-40 h-[600px] w-[600px] rounded-full bg-[var(--lime-glow)] opacity-[0.06] blur-[140px]" />
      <div className="absolute top-1/3 left-1/2 h-[400px] w-[400px] -translate-x-1/2 rounded-full bg-[var(--wheat)] opacity-[0.04] blur-[120px]" />

      {/* Grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.025]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 75%)",
        }}
      />

      {/* Floating particles */}
      {Array.from({ length: 14 }).map((_, i) => (
        <span
          key={i}
          className="particle absolute bottom-0 block h-1 w-1 rounded-full bg-[var(--lime-glow)]"
          style={{
            left: `${(i * 37) % 100}%`,
            animationDuration: `${18 + (i % 6) * 4}s`,
            animationDelay: `${(i * 1.7) % 12}s`,
            opacity: 0.4,
          }}
        />
      ))}
    </div>
  );
}
