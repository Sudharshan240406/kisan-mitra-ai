import { createFileRoute } from "@tanstack/react-router";
import { Users, Bot, Phone, MessageCircle, Landmark, MapPin, CloudSun, Sparkles } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Hero } from "@/components/kisan/Hero";
import { KpiCard, type Kpi } from "@/components/kisan/KpiCard";
import { AgentGrid } from "@/components/kisan/AgentGrid";
import { IndiaMap } from "@/components/kisan/IndiaMap";
import {
  WeatherPanel, MarketPanel, SchemesPanel, CommsPanel, AlertsPanel,
} from "@/components/kisan/Panels";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Kisan Mitra AI — Agriculture Operations OS" },
      { name: "description", content: "Premium AI-powered command center for Indian agriculture — farmers, weather, mandis, schemes, and neural agents in one operating system." },
      { property: "og:title", content: "Kisan Mitra AI — Agriculture Operations OS" },
      { property: "og:description", content: "Premium AI-powered command center for Indian agriculture — farmers, weather, mandis, schemes, and neural agents in one operating system." },
    ],
  }),
  component: Dashboard,
});

// KPI shells — values remain zero and sparklines are flat until the
// backend publishes real operational metrics.
const FLAT = Array(12).fill(0);
const kpis: Kpi[] = [
  { label: "Active Farmers", value: 0, delta: 0, icon: Users, tone: "lime", data: FLAT },
  { label: "AI Requests · 24h", value: 0, delta: 0, icon: Bot, tone: "sky", data: FLAT },
  { label: "Voice Calls Today", value: 0, delta: 0, icon: Phone, tone: "wheat", data: FLAT },
  { label: "SMS Dispatched", value: 0, delta: 0, icon: MessageCircle, tone: "leaf", data: FLAT },
  { label: "Schemes Processed", value: 0, delta: 0, icon: Landmark, tone: "wheat", data: FLAT },
  { label: "Active Villages", value: 0, delta: 0, icon: MapPin, tone: "leaf", data: FLAT },
  { label: "Weather Requests", value: 0, delta: 0, icon: CloudSun, tone: "sky", data: FLAT },
  { label: "AI Confidence", value: 0, suffix: "%", delta: 0, icon: Sparkles, tone: "lime", data: FLAT },
];

function Dashboard() {
  return (
    <AppShell>
      <Hero />

      <section aria-label="Key metrics">
        <div className="mb-3 flex items-end justify-between px-1">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
              Realtime metrics
            </div>
            <h2 className="mt-0.5 font-display text-lg font-bold sm:text-xl">Operations pulse</h2>
          </div>
          <div className="hidden items-center gap-1.5 text-[10px] text-mono text-white/50 sm:flex">
            <span className="size-1.5 rounded-full bg-white/30" />
            Waiting for backend
          </div>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-4">
          {kpis.map((k, i) => <KpiCard key={k.label} kpi={k} index={i} />)}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="xl:col-span-8 space-y-6">
          <IndiaMap />
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <WeatherPanel />
            <MarketPanel />
          </div>
        </div>
        <div className="xl:col-span-4 space-y-6">
          <AgentGrid />
          <AlertsPanel />
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <CommsPanel />
        </div>
        <SchemesPanel />
      </section>
    </AppShell>
  );
}
