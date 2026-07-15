import { Activity, PhoneCall, Users, Gauge, Zap, ServerCog, Cpu } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import type { TelemetryVitals } from "@/api/mission";

const toneMap = {
  lime: "text-[var(--lime-glow)]",
  sky: "text-[var(--sky-agri)]",
  wheat: "text-[var(--wheat)]",
} as const;

type Row = {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  tone: keyof typeof toneMap;
  value: string;
  pct: number | null;
};

function fmtInt(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}
function fmtPct(n: number | null): string {
  return n == null ? "—" : `${n.toFixed(2)}%`;
}
function fmtMs(n: number | null): string {
  return n == null ? "—" : `${Math.round(n)}ms`;
}

export function TelemetryPanel({ vitals }: { vitals: TelemetryVitals }) {
  const rows: Row[] = [
    { label: "Active calls", icon: PhoneCall, tone: "lime", value: fmtInt(vitals.activeCalls), pct: vitals.activeCalls == null ? null : Math.min(100, vitals.activeCalls / 10) },
    { label: "Active farmers", icon: Users, tone: "sky", value: fmtInt(vitals.activeFarmers), pct: vitals.activeFarmers == null ? null : Math.min(100, vitals.activeFarmers / 1000) },
    { label: "Avg AI latency", icon: Zap, tone: "wheat", value: fmtMs(vitals.avgLatencyMs), pct: vitals.avgLatencyMs == null ? null : Math.min(100, vitals.avgLatencyMs / 10) },
    { label: "Recommendations · today", icon: Activity, tone: "lime", value: fmtInt(vitals.recommendationsToday), pct: vitals.recommendationsToday == null ? null : Math.min(100, vitals.recommendationsToday / 100) },
    { label: "System health", icon: Gauge, tone: "sky", value: fmtPct(vitals.systemHealthPct), pct: vitals.systemHealthPct },
    { label: "CPU · GPU", icon: ServerCog, tone: "wheat", value: vitals.cpuPct == null && vitals.gpuPct == null ? "—" : `${vitals.cpuPct ?? "—"}% · ${vitals.gpuPct ?? "—"}%`, pct: vitals.cpuPct },
  ];

  const allEmpty = rows.every((r) => r.pct == null && r.value === "—");

  return (
    <GlassCard eyebrow="Live telemetry" title="Platform Vitals" strong>
      {allEmpty && (
        <div className="mb-3 flex items-center gap-2 rounded-xl border border-dashed border-white/10 p-3 text-[11px] text-white/50">
          <Cpu className="size-3.5 text-white/40" /> No telemetry received yet.
        </div>
      )}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {rows.map((s) => {
          const Icon = s.icon;
          const color = toneMap[s.tone];
          return (
            <div key={s.label} className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
              <div className="flex items-center justify-between">
                <span className="text-[9px] uppercase tracking-widest text-white/40">{s.label}</span>
                <Icon className={`size-3.5 ${color}`} />
              </div>
              <div className={`mt-1 font-display text-lg font-bold ${s.value === "—" ? "text-white/40" : color}`}>{s.value}</div>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[var(--lime-glow)] to-emerald-300 transition-all"
                  style={{ width: `${s.pct ?? 0}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </GlassCard>
  );
}
