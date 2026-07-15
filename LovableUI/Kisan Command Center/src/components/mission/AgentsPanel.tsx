import { Bot } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import type { AgentSnapshot } from "@/api/mission";

export function AgentsPanel({ agents }: { agents: AgentSnapshot[] }) {
  if (agents.length === 0) {
    return (
      <GlassCard eyebrow="Backend AI Fleet" title="Active Agents" strong>
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-8 text-center">
          <Bot className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">No agent telemetry received.</div>
          <div className="text-[11px] text-white/40">Agent status appears as soon as the backend reports it.</div>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard eyebrow="Backend AI Fleet" title="Active Agents" strong>
      <div className="grid gap-2 sm:grid-cols-2">
        {agents.map((a) => (
          <article
            key={a.id}
            className="group flex items-start gap-2.5 rounded-xl border border-white/5 bg-white/[0.02] p-2.5 transition hover:border-[var(--lime-glow)]/25"
          >
            <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-[var(--lime-glow)]/15 ring-1 ring-[var(--lime-glow)]/30">
              <Bot className="size-4 text-[var(--lime-glow)]" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <div className="truncate text-xs font-semibold">{a.name}</div>
                <StatusBadge
                  tone={a.status === "active" ? "lime" : a.status === "degraded" ? "wheat" : "muted"}
                  dot={a.status === "active"}
                >
                  {a.status}
                </StatusBadge>
              </div>
              <div className="text-[10px] text-mono text-white/40">{a.role}</div>
              <div className="mt-1 flex items-center justify-between text-[10px] text-mono">
                <span className="truncate text-white/60">{a.task}</span>
                <span className="text-[var(--sky-agri)]">{a.latencyMs}ms</span>
              </div>
            </div>
          </article>
        ))}
      </div>
    </GlassCard>
  );
}
