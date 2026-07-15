import { createFileRoute } from "@tanstack/react-router";
import { CloudSun, Wind, Droplets, Thermometer, Gauge, Sun } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { EmptyState } from "@/components/layout/EmptyState";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { weatherApi } from "@/api/weather";

export const Route = createFileRoute("/weather")({
  head: () => ({ meta: [{ title: "Weather Intelligence · Kisan Mitra" }] }),
  component: Page,
});

const DASH = "—";

function Page() {
  const summary = useResource(() => weatherApi.currentSummary(), []);
  const forecast = useResource(() => weatherApi.forecast7(), []);
  const alerts = useResource(() => weatherApi.alerts(), []);

  return (
    <AppShell>
      <PageHeader
        icon={CloudSun}
        eyebrow="IMD · ECMWF · Copernicus"
        title="Weather Intelligence"
        description="Hyperlocal forecasts, rainfall nowcasting, and agro-met advisories at village resolution."
      />

      <StatGrid stats={[
        { label: "Villages served", value: DASH, delta: "Waiting for backend", tone: "lime" },
        { label: "Forecast accuracy", value: DASH, delta: "Waiting for backend", tone: "sky" },
        { label: "Advisories · 24h", value: DASH, delta: "Waiting for backend", tone: "wheat" },
        { label: "Active alerts", value: DASH, delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <GlassCard title="Live conditions" eyebrow="Now" strong>
            <StateWrapper state={summary} emptyTitle="No weather data" emptyHint="Waiting for backend to publish live conditions.">
              {(s) => s ? (
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <Metric icon={Thermometer} tone="wheat" label="Temperature" value={s.tempC != null ? `${s.tempC.toFixed(1)}°C` : DASH} sub={s.feelsLike != null ? `feels ${s.feelsLike.toFixed(0)}°` : DASH} />
                  <Metric icon={Droplets} tone="sky" label="Humidity" value={s.humidity != null ? `${s.humidity}%` : DASH} sub={s.rainMm24h != null ? `rain 24h ${s.rainMm24h}mm` : DASH} />
                  <Metric icon={Wind} tone="lime" label="Wind" value={s.windKmh != null ? `${s.windKmh} km/h` : DASH} sub={DASH} />
                  <Metric icon={Gauge} tone="leaf" label="Pressure" value={s.pressureHpa != null ? `${s.pressureHpa}` : DASH} sub={s.cloudCover != null ? `hPa · cloud ${s.cloudCover}%` : "hPa"} />
                  <Metric icon={Sun} tone="wheat" label="UV Index" value={s.uvIndex != null ? `${s.uvIndex}` : DASH} sub={DASH} />
                  <Metric icon={Droplets} tone="sky" label="Dew point" value={s.dewPointC != null ? `${s.dewPointC}°C` : DASH} sub={DASH} />
                </div>
              ) : null}
            </StateWrapper>
          </GlassCard>

          <GlassCard title="7-day forecast" eyebrow="ECMWF ensemble" strong>
            <StateWrapper state={forecast} emptyTitle="No forecast available" emptyHint="Waiting for backend forecast feed.">
              {(days) => (
                <div className="grid grid-cols-7 gap-2">
                  {days.map((f) => (
                    <div key={f.day} className="rounded-xl bg-white/[0.03] p-3 text-center ring-1 ring-inset ring-white/5">
                      <div className="text-[10px] text-mono uppercase text-white/40">{f.day}</div>
                      <div className="text-[10px] text-white/40">{f.date}</div>
                      <div className="mt-1 font-display text-lg font-bold">{f.tempMax}°</div>
                      <div className="text-[10px] text-white/40">min {f.tempMin}°</div>
                      <div className="mt-1 text-[10px] text-[var(--sky-agri)]">☔ {f.rainProb}%</div>
                      <div className="text-[9px] text-white/40">{f.windKmh}km/h</div>
                    </div>
                  ))}
                </div>
              )}
            </StateWrapper>
          </GlassCard>
        </div>

        <GlassCard title="Active alerts" eyebrow="Advisory" strong>
          <StateWrapper state={alerts} emptyTitle="No weather alerts" emptyHint="Waiting for backend alert stream.">
            {(rows) => (
              <ul className="space-y-3">
                {rows.map((a) => (
                  <li key={a.id} className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold">{a.region}</span>
                      <StatusBadge tone={a.severity === "severe" ? "red" : a.severity === "warning" ? "wheat" : "sky"} dot>{a.validFor}</StatusBadge>
                    </div>
                    <div className="mt-1 text-xs text-white/60">{a.type}</div>
                    <div className="mt-1 text-[10px] text-mono text-white/40">issued {a.issuedAt}</div>
                  </li>
                ))}
              </ul>
            )}
          </StateWrapper>
        </GlassCard>
      </div>

      {/* Silence unused import warning in strict TS */}
      <div className="hidden"><EmptyState icon={CloudSun} title="" /></div>
    </AppShell>
  );
}

function Metric({ icon: Icon, tone, label, value, sub }: { icon: React.ComponentType<{ className?: string }>; tone: "lime" | "sky" | "wheat" | "leaf"; label: string; value: string; sub: string }) {
  const map = { lime: "text-[var(--lime-glow)]", sky: "text-[var(--sky-agri)]", wheat: "text-[var(--wheat)]", leaf: "text-emerald-300" };
  return (
    <div className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/40">{label}</span>
        <Icon className={`size-4 ${map[tone]}`} />
      </div>
      <div className="mt-1 font-display text-xl font-bold">{value}</div>
      <div className="text-[10px] text-white/40">{sub}</div>
    </div>
  );
}
