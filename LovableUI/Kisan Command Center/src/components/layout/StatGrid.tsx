import type { LucideIcon } from "lucide-react";

export type Stat = {
  label: string;
  value: string;
  delta?: string;
  icon?: LucideIcon;
  tone?: "lime" | "sky" | "wheat" | "leaf";
};

const toneMap = {
  lime: "text-[var(--lime-glow)]",
  sky: "text-[var(--sky-agri)]",
  wheat: "text-[var(--wheat)]",
  leaf: "text-emerald-300",
};

export function StatGrid({ stats }: { stats: Stat[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {stats.map((s) => {
        const Icon = s.icon;
        const tone = toneMap[s.tone ?? "lime"];
        return (
          <div
            key={s.label}
            className="glass-panel group relative overflow-hidden rounded-2xl border border-white/5 p-4 transition hover:border-[var(--lime-glow)]/25 hover:shadow-[0_0_30px_-12px_var(--lime-glow)]"
          >
            <div className="flex items-start justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
                {s.label}
              </span>
              {Icon && <Icon className={`size-4 ${tone}`} />}
            </div>
            <div className="mt-2 font-display text-2xl font-bold text-white">{s.value}</div>
            {s.delta && (
              <div className={`mt-1 text-[11px] text-mono ${tone}`}>{s.delta}</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
