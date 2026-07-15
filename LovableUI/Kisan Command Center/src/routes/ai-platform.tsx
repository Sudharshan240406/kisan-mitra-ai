import { createFileRoute } from "@tanstack/react-router";
import { Cpu, Zap, Database, Layers, Rocket, GitBranch, Activity } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { ActionButton } from "@/components/layout/ActionButton";
import { DataTable } from "@/components/layout/DataTable";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { aiApi, type Model, type Provider } from "@/api/ai";

export const Route = createFileRoute("/ai-platform")({
  head: () => ({ meta: [{ title: "AI Platform · Kisan Mitra" }, { name: "description", content: "Foundation models, inference infra, and MLOps pipeline for Kisan Mitra AI." }] }),
  component: Page,
});

function Page() {
  const providers = useResource(() => aiApi.providers(), []);
  const models = useResource(() => aiApi.models(), []);
  const routing = useResource(() => aiApi.routingDecisions(), []);

  return (
    <AppShell>
      <PageHeader
        icon={Cpu}
        eyebrow="Infrastructure"
        title="AI Platform"
        description="Foundation models, GPU fleet, and MLOps pipelines powering the Kisan Mitra intelligence layer."
        actions={<><ActionButton icon={GitBranch}>Deployments</ActionButton><ActionButton icon={Rocket} variant="primary">Deploy model</ActionButton></>}
      />

      <StatGrid stats={[
        { label: "Models in prod", value: "—", delta: "Waiting for backend", icon: Layers, tone: "lime" },
        { label: "GPU Fleet", value: "—", delta: "Waiting for backend", icon: Zap, tone: "sky" },
        { label: "Inferences · 24h", value: "—", delta: "Waiting for backend", icon: Cpu, tone: "wheat" },
        { label: "Vector DB", value: "—", delta: "Waiting for backend", icon: Database, tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Providers · live health" eyebrow="Gateway" className="lg:col-span-2" strong>
          <StateWrapper state={providers}>
            {(rows) => (
              <DataTable<Provider>
                columns={[
                  { key: "name", header: "Provider", render: (r) => <span className="font-semibold text-white">{r.name}</span> },
                  { key: "region", header: "Region", render: (r) => <span className="text-mono text-[11px] text-white/60">{r.region}</span> },
                  { key: "latencyMs", header: "p95", render: (r) => <span className="text-mono text-[var(--sky-agri)]">{r.latencyMs}ms</span> },
                  { key: "requests24h", header: "Req · 24h", render: (r) => <span className="text-mono">{(r.requests24h / 1e6).toFixed(2)}M</span> },
                  { key: "errorRate", header: "Errors", render: (r) => <span className={r.errorRate > 1 ? "text-mono text-red-300" : "text-mono text-emerald-300"}>{r.errorRate}%</span> },
                  { key: "cost24hUsd", header: "Cost · 24h", render: (r) => <span className="text-mono text-[var(--wheat)]">${r.cost24hUsd.toFixed(0)}</span> },
                  { key: "status", header: "Status", render: (r) => <StatusBadge tone={r.status === "healthy" ? "lime" : r.status === "degraded" ? "wheat" : "red"} dot>{r.status}</StatusBadge> },
                ]}
                rows={rows}
              />
            )}
          </StateWrapper>
        </GlassCard>

        <GlassCard title="Pipeline health" eyebrow="MLOps" strong>
          <div className="grid min-h-[160px] place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center">
            <div>
              <Activity className="mx-auto size-6 text-white/40" />
              <div className="mt-2 text-sm font-semibold text-white/80">No pipeline telemetry</div>
              <div className="mt-1 text-xs text-white/50">Waiting for backend MLOps stream.</div>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Model registry" eyebrow="Production" className="lg:col-span-2" strong>
          <StateWrapper state={models}>
            {(rows) => (
              <div className="space-y-2">
                {rows.map((m) => (
                  <div key={m.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-semibold">{m.name}</div>
                      <div className="text-[11px] text-mono text-white/40">
                        {m.kind} · {m.provider} · p95 {m.p95LatencyMs}ms {m.fallback && <>· fallback: <span className="text-[var(--wheat)]">{m.fallback}</span></>}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-[10px] text-mono uppercase text-white/40">Confidence</div>
                        <div className="text-mono text-sm text-[var(--lime-glow)]">{(m.confidence * 100).toFixed(0)}%</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] text-mono uppercase text-white/40">24h Cost</div>
                        <div className="text-mono text-sm text-[var(--wheat)]">${m.costUsd.toFixed(0)}</div>
                      </div>
                      <StatusBadge tone={m.status === "healthy" ? "lime" : m.status === "degraded" ? "wheat" : "red"} dot>{m.status}</StatusBadge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </StateWrapper>
        </GlassCard>

        <GlassCard title="Routing decisions · last hour" eyebrow="Fallback" strong>
          <StateWrapper state={routing}>
            {(rows) => (
              <ul className="space-y-3 text-xs">
                {rows.map((r, i) => (
                  <li key={i} className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                    <div className="flex items-center justify-between">
                      <span className="text-mono text-white/40">{r.at}</span>
                      <StatusBadge tone="sky">{r.count} calls</StatusBadge>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-white/80">
                      <Activity className="size-3 text-[var(--sky-agri)]" />
                      <span className="font-semibold">{r.from}</span>
                      <span className="text-white/40">→</span>
                      <span className="font-semibold text-[var(--wheat)]">{r.to}</span>
                    </div>
                    <div className="mt-1 text-[11px] text-white/50">{r.reason}</div>
                  </li>
                ))}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>
      </div>
    </AppShell>
  );
}
