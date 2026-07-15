import { createFileRoute } from "@tanstack/react-router";
import { Landmark, FileCheck2, CheckCircle2, Circle, CalendarClock } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { DataTable } from "@/components/layout/DataTable";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { schemesApi, type Scheme } from "@/api/schemes";

export const Route = createFileRoute("/schemes")({
  head: () => ({ meta: [{ title: "Government Schemes · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const schemes = useResource(() => schemesApi.list(), []);
  const applications = useResource(() => schemesApi.applications(), []);
  const eligibility = useResource(() => schemesApi.eligibility("KM-84210"), []);

  return (
    <AppShell>
      <PageHeader
        icon={Landmark}
        eyebrow="Central + State portals"
        title="Government Schemes"
        description="Auto-eligibility check, application filing, and DBT disbursal tracking for 42 agri schemes."
      />

      <StatGrid stats={[
        { label: "Applications", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "Approvals · 30d", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "DBT disbursed", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Grievances open", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Active schemes" eyebrow="Portfolio" className="lg:col-span-2" strong>
          <StateWrapper state={schemes}>
            {(rows) => (
              <div className="space-y-2">
                {rows.map((s: Scheme) => (
                  <div key={s.id} className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <StatusBadge tone="lime">{s.id}</StatusBadge>
                          <span className="truncate text-sm font-semibold">{s.name}</span>
                        </div>
                        <div className="mt-1 text-[11px] text-white/50">{s.ministry} · {s.benefit}</div>
                      </div>
                      <div className="flex items-center gap-3 text-right">
                        <div>
                          <div className="text-[10px] text-mono uppercase text-white/40">Enrolled</div>
                          <div className="text-sm font-bold text-[var(--lime-glow)]">{s.enrolled.toLocaleString("en-IN")}</div>
                        </div>
                        <StatusBadge tone={s.status === "Open" ? "lime" : s.status === "Closing soon" ? "wheat" : "muted"} dot>{s.status}</StatusBadge>
                      </div>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-3">
                      <MetaBlock icon={CheckCircle2} label="Eligibility" items={s.eligibility} />
                      <MetaBlock icon={FileCheck2} label="Documents" items={s.documents} />
                      <div className="rounded-lg bg-white/[0.02] p-2 ring-1 ring-inset ring-white/5">
                        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
                          <CalendarClock className="size-3 text-[var(--lime-glow)]" /> Deadline
                        </div>
                        <div className="mt-1 text-xs text-white/80">{s.deadline}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </StateWrapper>
        </GlassCard>

        <GlassCard title="Eligibility · KM-84210" eyebrow="Auto-checker" strong>
          <StateWrapper state={eligibility}>
            {(rows) => (
              <ul className="space-y-2 text-sm">
                {rows.map((r) => (
                  <li key={r.id} className="flex items-start gap-2 rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                    {r.eligible ? <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-[var(--lime-glow)]" /> : <Circle className="mt-0.5 size-4 shrink-0 text-white/40" />}
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white">{r.name}</div>
                      <div className="text-[11px] text-white/50">{r.reason}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>
      </div>

      <GlassCard title="Application pipeline" eyebrow="Live status" strong>
        <StateWrapper state={applications}>
          {(rows) => (
            <DataTable
              columns={[
                { key: "id", header: "App ID", render: (r) => <span className="text-mono text-[11px] text-[var(--lime-glow)]">{r.id}</span> },
                { key: "farmer", header: "Farmer" },
                { key: "scheme", header: "Scheme" },
                { key: "stage", header: "Stage", render: (r) => <StatusBadge tone={r.stage === "Disbursed" ? "lime" : r.stage === "Approved" ? "sky" : r.stage === "Verification" ? "wheat" : "muted"} dot>{r.stage}</StatusBadge> },
                { key: "updatedAt", header: "Updated" },
              ]}
              rows={rows}
            />
          )}
        </StateWrapper>
      </GlassCard>
    </AppShell>
  );
}

function MetaBlock({ icon: Icon, label, items }: { icon: React.ComponentType<{ className?: string }>; label: string; items: string[] }) {
  return (
    <div className="rounded-lg bg-white/[0.02] p-2 ring-1 ring-inset ring-white/5">
      <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">
        <Icon className="size-3 text-[var(--lime-glow)]" /> {label}
      </div>
      <ul className="mt-1 space-y-0.5 text-[11px] text-white/70">
        {items.map((i) => <li key={i}>· {i}</li>)}
      </ul>
    </div>
  );
}
