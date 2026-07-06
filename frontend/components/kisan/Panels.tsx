"use client";

import React from "react";
import { useDashboard } from "@/components/DashboardContext";
import {
  CloudSun,
  TrendingUp,
  Landmark,
  AlertTriangle,
  Activity,
  Inbox,
  CheckCircle2,
  Phone,
  Mail
} from "lucide-react";

/* ─────────────  WEATHER  ───────────── */
export function WeatherPanel() {
  const { integrations } = useDashboard();
  const weatherAdapters = integrations.filter(i => i.type === "weather");

  return (
    <PanelShell eyebrow="Meteorology" title="Weather Adapters" icon={<CloudSun className="size-4" />}>
      {weatherAdapters.length > 0 ? (
        <div className="flex flex-col gap-2">
          {weatherAdapters.map((wa) => (
            <div key={wa.id} className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl flex items-center justify-between text-[11px]">
              <div>
                <p className="font-bold text-slate-200">{wa.name}</p>
                <p className="text-[9px] text-slate-500 font-mono mt-0.5">{wa.configuration?.api_endpoint || "Local Adapter"}</p>
              </div>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase ${
                wa.status === "active" ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-900 text-slate-550"
              }`}>{wa.status}</span>
            </div>
          ))}
        </div>
      ) : (
        <Empty label="No weather feeds active" hint="Ensure weather station integration is enabled." />
      )}
    </PanelShell>
  );
}

/* ─────────────  MARKET  ───────────── */
export function MarketPanel() {
  const { integrations } = useDashboard();
  const marketAdapters = integrations.filter(i => i.type === "market");

  return (
    <PanelShell eyebrow="Mandi Feed" title="Market Pricing feeds" icon={<TrendingUp className="size-4" />}>
      {marketAdapters.length > 0 ? (
        <div className="flex flex-col gap-2">
          {marketAdapters.map((ma) => (
            <div key={ma.id} className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl flex items-center justify-between text-[11px]">
              <div>
                <p className="font-bold text-slate-200">{ma.name}</p>
                <p className="text-[9px] text-slate-500 font-mono mt-0.5">{ma.description}</p>
              </div>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase ${
                ma.status === "active" ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-900 text-slate-550"
              }`}>{ma.status}</span>
            </div>
          ))}
        </div>
      ) : (
        <Empty label="No market feeds active" hint="Ensure market pricing adapters are configured." />
      )}
    </PanelShell>
  );
}

/* ─────────────  SCHEMES  ───────────── */
export function SchemesPanel() {
  const { calls, integrations } = useDashboard();
  const schemeAdapters = integrations.filter(i => i.type === "schemes" || i.type === "welfare");

  return (
    <PanelShell eyebrow="Government" title="Welfare Registries" icon={<Landmark className="size-4" />}>
      {schemeAdapters.length > 0 ? (
        <div className="flex flex-col gap-2">
          {schemeAdapters.map((sa) => (
            <div key={sa.id} className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl flex items-center justify-between text-[11px]">
              <div>
                <p className="font-bold text-slate-200">{sa.name}</p>
                <p className="text-[9px] text-slate-500 font-mono mt-0.5">{sa.capabilities.join(", ") || "Eligibility check"}</p>
              </div>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase ${
                sa.status === "active" ? "bg-emerald-500/10 text-emerald-400" : "bg-slate-900 text-slate-550"
              }`}>{sa.status}</span>
            </div>
          ))}
        </div>
      ) : (
        <Empty label="No welfare feeds active" hint="Connect to welfare scheme databases." />
      )}
    </PanelShell>
  );
}

/* ─────────────  COMMS  ───────────── */
export function CommsPanel() {
  const { calls, smsSessions } = useDashboard();

  const activeCalls = calls.filter(c => c.status !== "completed");
  const activeSms = smsSessions.filter(s => s.state !== "closed");

  return (
    <PanelShell eyebrow="Communications" title="Voice & SMS Sessions" icon={<Activity className="size-4" />}>
      {(activeCalls.length > 0 || activeSms.length > 0) ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {/* Active calls */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider block mb-1">Active Call Trunks</span>
            {activeCalls.map((call) => (
              <div key={call.call_id} className="p-3 bg-slate-950/50 border border-slate-900 rounded-xl flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                  <div>
                    <p className="font-bold text-slate-200">{call.caller}</p>
                    <p className="text-[9px] text-slate-500 font-mono">State: {call.current_ivr_state}</p>
                  </div>
                </div>
                <span className="text-[8px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded uppercase font-bold tracking-wider animate-pulse">Live</span>
              </div>
            ))}
            {activeCalls.length === 0 && (
              <p className="text-[10px] text-slate-600 italic py-2">No live IVR calls</p>
            )}
          </div>

          {/* Active SMS */}
          <div className="flex flex-col gap-2">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider block mb-1">SMS Queue sessions</span>
            {activeSms.map((sms) => (
              <div key={sms.sms_session_id} className="p-3 bg-slate-950/50 border border-slate-900 rounded-xl flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <Mail className="w-3.5 h-3.5 text-sky-400" />
                  <div>
                    <p className="font-bold text-slate-200">{sms.phone_number}</p>
                    <p className="text-[9px] text-slate-500 font-mono">Delivery: {sms.delivery_status}</p>
                  </div>
                </div>
                <span className="text-[8px] bg-slate-900 text-slate-400 px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">{sms.state}</span>
              </div>
            ))}
            {activeSms.length === 0 && (
              <p className="text-[10px] text-slate-600 italic py-2">No active SMS threads</p>
            )}
          </div>
        </div>
      ) : (
        <Empty label="No active channels telemetry" hint="Telemetry links will activate on incoming telephony/SMS triggers." />
      )}
    </PanelShell>
  );
}

/* ─────────────  ALERTS  ───────────── */
export function AlertsPanel() {
  const { alerts } = useDashboard();

  return (
    <PanelShell eyebrow="Live feed" title="Realtime System Alerts" icon={<AlertTriangle className="size-4" />}>
      {alerts.length > 0 ? (
        <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1 mc-scrollbar">
          {alerts.map((alert, idx) => (
            <div key={idx} className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl flex items-start gap-2.5 text-[11px]">
              <AlertTriangle className={`w-4 h-4 shrink-0 mt-0.5 ${
                alert.type === "error" ? "text-red-400" : alert.type === "warn" ? "text-amber-400" : "text-sky-400"
              }`} />
              <div>
                <div className="flex justify-between items-center gap-2">
                  <span className={`font-bold uppercase text-[9px] ${
                    alert.type === "error" ? "text-red-400" : alert.type === "warn" ? "text-amber-400" : "text-sky-400"
                  }`}>{alert.type}</span>
                  <span className="text-[8px] text-slate-600 font-mono">{alert.time}</span>
                </div>
                <p className="text-slate-300 mt-1">{alert.msg}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Empty label="No alerts active" hint="Telemetry listening. Platform healthy." />
      )}
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
    <div className="glass-panel h-full rounded-3xl p-5 z-10">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <div className="text-[9px] font-black uppercase tracking-[0.18em] text-[var(--lime-glow)]">
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
        <div className="mt-2 text-xs font-semibold text-white/80">{label}</div>
        <div className="mt-1 text-[10px] text-white/50">{hint}</div>
      </div>
    </div>
  );
}
