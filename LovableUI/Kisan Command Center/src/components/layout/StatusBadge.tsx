type Tone = "lime" | "sky" | "wheat" | "leaf" | "red" | "muted";

const map: Record<Tone, string> = {
  lime: "bg-[var(--lime-glow)]/15 text-[var(--lime-glow)] ring-[var(--lime-glow)]/30",
  sky: "bg-[var(--sky-agri)]/15 text-[var(--sky-agri)] ring-[var(--sky-agri)]/30",
  wheat: "bg-[var(--wheat)]/15 text-[var(--wheat)] ring-[var(--wheat)]/30",
  leaf: "bg-emerald-400/15 text-emerald-300 ring-emerald-400/30",
  red: "bg-red-500/15 text-red-300 ring-red-400/30",
  muted: "bg-white/5 text-white/60 ring-white/10",
};

export function StatusBadge({
  tone = "lime",
  children,
  dot,
}: {
  tone?: Tone;
  children: React.ReactNode;
  dot?: boolean;
}) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-semibold ring-1 ring-inset",
        map[tone],
      ].join(" ")}
    >
      {dot && <span className="size-1.5 rounded-full bg-current animate-pulse-soft" />}
      {children}
    </span>
  );
}
