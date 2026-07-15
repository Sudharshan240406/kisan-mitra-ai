import { createFileRoute } from "@tanstack/react-router";
import { Radio, Cpu, MemoryStick, Zap, AlertOctagon } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { telemetryApi, type ServiceHealth } from "@/api/telemetry";

export const Route = createFileRoute("/telemetry")({
  head: () => ({ meta: [{ title: "Telemetry · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  const services = useResource(() => telemetryApi.services(), []);
  const history = useResource(() => telemetryApi.history(), []);

  return (
    <AppShell>
      <PageHeader
        icon={Radio}
        eyebrow="Observability"
        title="Telemetry"
        description="Live SLO dashboard with request rate, latency percentiles, and error budgets across every service."
      />

      <StatGrid stats={[
        { label: "CPU", value: DASH, delta: "Waiting for backend", icon: Cpu, tone: "lime" },
        { label: "Memory", value: DASH, delta: "Waiting for backend", icon: MemoryStick, tone: "sky" },
        { label: "Req · 1m", value: DASH, delta: "Waiting for backend", icon: Zap, tone: "wheat" },
        { label: "Errors · 1m", value: DASH, delta: "Waiting for backend", icon: AlertOctagon, tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Requests per minute" eyebrow="Live · 30m" className="lg:col-span-2" strong>
          <StateWrapper state={history} emptyTitle="No telemetry received yet" emptyHint="Waiting for backend metrics stream.">{() => null}</StateWrapper>
        </GlassCard>
        <GlassCard title="Errors per minute" eyebrow="Live · 30m" strong>
          <StateWrapper state={history} emptyTitle="No telemetry received yet" emptyHint="Waiting for backend metrics stream.">{() => null}</StateWrapper>
        </GlassCard>
      </div>

      <GlassCard title="Service health" eyebrow="SLO" strong>
        <StateWrapper state={services} emptyTitle="No service telemetry" emptyHint="Waiting for backend health probes.">
          {(rows) => (
            <div className="space-y-2">
              {rows.map((s: ServiceHealth) => (
                <div key={s.name} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                  <div>
                    <div className="text-sm font-semibold">{s.name}</div>
                    <div className="text-[11px] text-mono text-white/40">uptime {s.uptime} · p95 {s.p95}ms</div>
                  </div>
                  <StatusBadge tone={s.status === "healthy" ? "lime" : s.status === "degraded" ? "wheat" : "red"} dot>{s.status}</StatusBadge>
                </div>
              ))}
            </div>
          )}
        </StateWrapper>
      </GlassCard>
    </AppShell>
  );
}
