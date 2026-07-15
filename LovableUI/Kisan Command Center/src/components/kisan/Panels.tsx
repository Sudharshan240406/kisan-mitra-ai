import {
  CloudSun, TrendingUp, Landmark, AlertTriangle, Activity, Inbox,
} from "lucide-react";

/* ─────────────  WEATHER  ───────────── */
export function WeatherPanel() {
  return (
    <PanelShell eyebrow="Meteorology" title="Weather · 7-day" icon={<CloudSun className="size-4" />}>
      <Empty label="No weather data" hint="Waiting for backend forecast feed." />
    </PanelShell>
  );
}

/* ─────────────  MARKET  ───────────── */
export function MarketPanel() {
  return (
    <PanelShell eyebrow="Mandi feed" title="Market Prices" icon={<TrendingUp className="size-4" />}>
      <Empty label="No market feed" hint="Waiting for backend mandi prices." />
    </PanelShell>
  );
}

/* ─────────────  SCHEMES  ───────────── */
export function SchemesPanel() {
  return (
    <PanelShell eyebrow="Government" title="Scheme Distribution" icon={<Landmark className="size-4" />}>
      <Empty label="No government scheme data" hint="Waiting for backend scheme feed." />
    </PanelShell>
  );
}

/* ─────────────  COMMS  ───────────── */
export function CommsPanel() {
  return (
    <PanelShell eyebrow="Communications" title="Voice · SMS Throughput" icon={<Activity className="size-4" />}>
      <Empty label="No Data Available" hint="Waiting for backend throughput telemetry." />
    </PanelShell>
  );
}

/* ─────────────  ALERTS  ───────────── */
export function AlertsPanel() {
  return (
    <PanelShell eyebrow="Live" title="System Alerts" icon={<AlertTriangle className="size-4" />}>
      <Empty label="No alerts" hint="Waiting for backend alert stream." />
    </PanelShell>
  );
}

/* ─────────────  helpers  ───────────── */
function PanelShell({
  eyebrow, title, icon, children,
}: {
  eyebrow: string; title: string; icon?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="glass-panel h-full rounded-3xl p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
            {eyebrow}
          </div>
          <h3 className="mt-0.5 font-display text-base font-bold sm:text-lg">{title}</h3>
        </div>
        {icon && <div className="grid size-8 place-items-center rounded-lg bg-white/5 text-white/70">{icon}</div>}
      </div>
      {children}
    </div>
  );
}

function Empty({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="grid min-h-[160px] place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center">
      <div>
        <Inbox className="mx-auto size-6 text-white/40" />
        <div className="mt-2 text-sm font-semibold text-white/80">{label}</div>
        <div className="mt-1 text-xs text-white/50">{hint}</div>
      </div>
    </div>
  );
}
