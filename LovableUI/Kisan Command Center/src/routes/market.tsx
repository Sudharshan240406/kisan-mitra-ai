import { createFileRoute } from "@tanstack/react-router";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { DataTable } from "@/components/layout/DataTable";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { AreaSpark } from "@/components/layout/Charts";
import { useResource } from "@/hooks/useResource";
import { marketApi, type MandiPrice } from "@/api/market";

export const Route = createFileRoute("/market")({
  head: () => ({ meta: [{ title: "Market Intelligence · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const prices = useResource(() => marketApi.prices(), []);
  const gainers = useResource(() => marketApi.gainers(), []);
  const losers = useResource(() => marketApi.losers(), []);
  const [selected, setSelected] = useState("Cotton");
  const history = useResource(() => marketApi.history(selected), [selected]);

  return (
    <AppShell>
      <PageHeader
        icon={TrendingUp}
        eyebrow="Agmarknet · eNAM · Private feeds"
        title="Market Intelligence"
        description="Real-time mandi prices across 3,200+ markets with 7-day AI forecasts and arbitrage signals."
      />

      <StatGrid stats={[
        { label: "Mandis tracked", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "Commodities", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "Forecast MAPE", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Price alerts", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-2">
        <GlassCard title="Top gainers · 24h" eyebrow="Bull signals" strong>
          <StateWrapper state={gainers}>
            {(rows) => (
              <ul className="space-y-2">
                {rows.map((r) => <MoverRow key={r.commodity} row={r} up />)}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>
        <GlassCard title="Top losers · 24h" eyebrow="Bear signals" strong>
          <StateWrapper state={losers}>
            {(rows) => (
              <ul className="space-y-2">
                {rows.map((r) => <MoverRow key={r.commodity} row={r} />)}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <GlassCard title="Live mandi prices" eyebrow="Snapshot" className="lg:col-span-2" strong>
          <StateWrapper state={prices}>
            {(rows) => (
              <DataTable<MandiPrice>
                columns={[
                  { key: "commodity", header: "Commodity", render: (r) => (
                    <button onClick={() => setSelected(r.commodity)} className="text-left font-semibold text-white hover:text-[var(--lime-glow)]">{r.commodity}</button>
                  ) },
                  { key: "mandi", header: "Mandi", render: (r) => <span>{r.mandi}, {r.state}</span> },
                  { key: "priceQuintal", header: "Price", render: (r) => <span className="text-mono text-[var(--lime-glow)]">₹{r.priceQuintal.toLocaleString("en-IN")} /q</span> },
                  { key: "change24h", header: "Δ 24h", render: (r) => (
                    <span className={`inline-flex items-center gap-1 text-mono ${r.change24h >= 0 ? "text-emerald-300" : "text-red-300"}`}>
                      {r.change24h >= 0 ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                      {r.change24h > 0 ? "+" : ""}{r.change24h}%
                    </span>
                  ) },
                  { key: "forecast7d", header: "7d forecast", render: (r) => <span className="text-mono text-[var(--wheat)]">₹{r.forecast7d.toLocaleString("en-IN")}</span> },
                  { key: "demand", header: "Demand", render: (r) => <StatusBadge tone={r.demand === "Surging" || r.demand === "High" ? "lime" : r.demand === "Low" ? "wheat" : "sky"} dot>{r.demand}</StatusBadge> },
                ]}
                rows={rows}
              />
            )}
          </StateWrapper>
        </GlassCard>

        <GlassCard title={`${selected} · 30-day trend`} eyebrow="Price history" strong>
          <StateWrapper state={history}>
            {(rows) => <AreaSpark height={220} data={rows.map((r) => ({ x: `${r.day}`, y: r.price }))} />}
          </StateWrapper>
          <div className="mt-3 text-[11px] text-white/50">Tip: click any commodity in the table to chart it here.</div>
        </GlassCard>
      </div>
    </AppShell>
  );
}

function MoverRow({ row, up }: { row: MandiPrice; up?: boolean }) {
  return (
    <li className="flex items-center justify-between rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
      <div>
        <div className="text-sm font-semibold text-white">{row.commodity}</div>
        <div className="text-[11px] text-white/50">{row.mandi} · {row.state}</div>
      </div>
      <div className="text-right">
        <div className="text-mono text-sm text-[var(--lime-glow)]">₹{row.priceQuintal.toLocaleString("en-IN")}</div>
        <div className={`inline-flex items-center gap-1 text-mono text-xs ${up ? "text-emerald-300" : "text-red-300"}`}>
          {up ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
          {row.change24h > 0 ? "+" : ""}{row.change24h}%
        </div>
      </div>
    </li>
  );
}
