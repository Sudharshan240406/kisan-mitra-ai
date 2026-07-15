import { createFileRoute } from "@tanstack/react-router";
import { Bell, Check } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { alertsApi, type Alert } from "@/api/alerts";

export const Route = createFileRoute("/alerts")({
  head: () => ({ meta: [{ title: "Alerts · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  const alerts = useResource(() => alertsApi.list(), []);

  return (
    <AppShell>
      <PageHeader
        icon={Bell}
        eyebrow="Realtime notifications"
        title="Alerts"
        description="Rule-based and anomaly-driven alerts with escalation policies and multi-channel dispatch."
      />

      <StatGrid stats={[
        { label: "Active alerts", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Rules", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Notifications · 24h", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "MTTA", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard title="Live alerts" eyebrow="Inbox" strong>
          <StateWrapper state={alerts} emptyTitle="No alerts" emptyHint="Waiting for backend alert stream.">
            {(rows) => (
              <ul className="space-y-2">
                {rows.map((a: Alert) => (
                  <li key={a.id} className={`rounded-xl p-3 ring-1 ring-inset ${a.severity === "critical" ? "bg-red-500/[0.06] ring-red-500/25" : "bg-white/[0.03] ring-white/5"}`}>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-sm font-semibold text-white">{a.title}</div>
                        <div className="mt-0.5 text-xs text-white/60">{a.description}</div>
                        <div className="mt-1 text-[10px] text-mono text-white/40">{a.createdAt}{a.region ? ` · ${a.region}` : ""}</div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <StatusBadge tone={a.severity === "critical" ? "red" : a.severity === "warning" ? "wheat" : "sky"} dot>{a.severity}</StatusBadge>
                        {a.acknowledged ? <span className="inline-flex items-center gap-1 text-[10px] text-emerald-300"><Check className="size-3" /> ack</span> : <button className="text-[10px] text-white/60 hover:text-white">acknowledge</button>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>

        <GlassCard title="Alert rules" eyebrow="Policy" strong>
          <div className="grid min-h-[160px] place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center">
            <div>
              <Bell className="mx-auto size-6 text-white/40" />
              <div className="mt-2 text-sm font-semibold text-white/80">No alert rules loaded</div>
              <div className="mt-1 text-xs text-white/50">Waiting for backend rule registry.</div>
            </div>
          </div>
        </GlassCard>
      </div>
    </AppShell>
  );
}
