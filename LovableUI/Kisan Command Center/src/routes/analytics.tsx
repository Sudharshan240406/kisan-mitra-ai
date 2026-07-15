import { createFileRoute } from "@tanstack/react-router";
import { BarChart3 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { CommsPanel } from "@/components/kisan/Panels";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { AreaSpark, MiniBars } from "@/components/layout/Charts";
import { useResource } from "@/hooks/useResource";
import { analyticsApi } from "@/api/analytics";

export const Route = createFileRoute("/analytics")({
  head: () => ({ meta: [{ title: "Analytics · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const growth = useResource(() => analyticsApi.farmerGrowth(), []);
  const districts = useResource(() => analyticsApi.districts(), []);
  const schemes = useResource(() => analyticsApi.schemeUtilization(), []);
  return (
    <AppShell>
      <PageHeader
        icon={BarChart3}
        eyebrow="Product analytics"
        title="Analytics"
        description="Cross-channel engagement, cohort retention, and impact metrics for the Kisan Mitra platform."
      />

      <StatGrid stats={[
        { label: "MAU", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "DAU / MAU", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "Sessions · 24h", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Advisory → act", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Farmer growth · 6 months" eyebrow="Enrolments" className="lg:col-span-2" strong>
          <StateWrapper state={growth}>
            {(rows) => <AreaSpark height={220} data={rows.map((r) => ({ x: r.month, y: r.farmers }))} />}
          </StateWrapper>
        </GlassCard>
        <GlassCard title="Scheme utilization" eyebrow="% eligible" strong>
          <StateWrapper state={schemes}>
            {(rows) => <MiniBars height={220} data={rows.map((r) => ({ x: r.scheme, y: r.pct }))} />}
          </StateWrapper>
        </GlassCard>
      </div>

      <GlassCard title="District comparison" eyebrow="Top 5" strong>
        <StateWrapper state={districts}>
          {(rows) => (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              {rows.map((d) => (
                <div key={d.district} className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                  <div className="text-[10px] text-mono uppercase text-white/40">{d.state}</div>
                  <div className="mt-0.5 font-display text-sm font-bold">{d.district}</div>
                  <div className="mt-2 text-[11px] text-white/60">{d.farmers.toLocaleString("en-IN")} farmers</div>
                  <div className="mt-1 text-[11px] text-[var(--lime-glow)]">adoption {d.adoption}%</div>
                  <div className="text-[11px] text-emerald-300">yield +{d.avgYieldChange}%</div>
                </div>
              ))}
            </div>
          )}
        </StateWrapper>
      </GlassCard>

      <CommsPanel />
    </AppShell>
  );
}
