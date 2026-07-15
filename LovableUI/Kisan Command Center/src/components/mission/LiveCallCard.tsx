import { PhoneCall, Signal, Mic, Radio, MapPin, Sprout, Languages, Clock, PhoneOff } from "lucide-react";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { VoiceWaveform } from "./VoiceWaveform";
import type { LiveCall } from "@/api/mission";
import { STAGES } from "@/api/mission";

function fmt(sec: number) {
  const m = Math.floor(sec / 60).toString().padStart(2, "0");
  const s = (sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function LiveCallCard({ call }: { call: LiveCall | null }) {
  if (!call) return <WaitingCallCard />;

  const stageLabel = STAGES.find((s) => s.id === call.currentStage)?.label ?? "—";

  return (
    <section className="glass-panel-strong relative overflow-hidden rounded-3xl border border-white/5 p-5 sm:p-6">
      <div
        className="pointer-events-none absolute -inset-1 opacity-60"
        style={{ background: "radial-gradient(600px circle at 20% 0%, oklch(0.88 0.22 125 / 12%), transparent 60%)" }}
      />

      <div className="relative grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto]">
        <div className="min-w-0 space-y-4">
          <div className="flex items-center gap-2">
            <StatusBadge tone="red" dot>Live · IVR</StatusBadge>
            <StatusBadge tone="lime" dot>{stageLabel}</StatusBadge>
            <span className="text-mono text-[10px] text-white/40">{call.id}</span>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative grid size-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-[var(--lime-glow)]/25 to-[var(--forest-800)]/40 font-display text-lg font-bold text-white ring-1 ring-[var(--lime-glow)]/30">
              {call.farmer.avatarInitials}
              <span className="absolute -bottom-1 -right-1 grid size-5 place-items-center rounded-full bg-[var(--lime-glow)] text-[var(--forest-950)] ring-2 ring-[var(--forest-950)]">
                <PhoneCall className="size-2.5" />
              </span>
            </div>
            <div className="min-w-0">
              <h2 className="truncate font-display text-xl font-bold sm:text-2xl">{call.farmer.name}</h2>
              <div className="text-mono text-[11px] text-white/50">{call.farmer.phone}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px] sm:grid-cols-4">
            <Chip icon={MapPin} label="State" value={call.farmer.state} />
            <Chip icon={MapPin} label="District" value={call.farmer.district} />
            <Chip icon={Sprout} label="Crop" value={call.farmer.crop} />
            <Chip icon={Languages} label="Language" value={call.farmer.language} />
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Metric icon={Clock} label="Duration" value={fmt(call.durationSec)} tone="lime" />
            <Metric icon={Signal} label="Latency" value={`${call.latencyMs}ms`} tone="sky" />
            <Metric icon={Radio} label="Connection" value={call.connection} tone="wheat" />
          </div>
        </div>

        <div className="flex min-w-[240px] flex-col items-center justify-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] p-4">
          <div className="relative grid size-16 place-items-center rounded-full bg-gradient-to-br from-[var(--lime-glow)]/20 to-transparent ring-1 ring-[var(--lime-glow)]/40">
            <span className="absolute inset-0 rounded-full ring-2 ring-[var(--lime-glow)]/30 animate-ping" />
            <Mic className="size-7 text-[var(--lime-glow)]" />
          </div>
          <VoiceWaveform tone="lime" className="w-full" />
          <div className="text-mono text-[10px] uppercase tracking-widest text-white/50">
            Voice channel · awaiting audio frames
          </div>
        </div>
      </div>
    </section>
  );
}

function WaitingCallCard() {
  return (
    <section className="glass-panel-strong relative overflow-hidden rounded-3xl border border-white/5 p-6 sm:p-8">
      <div
        className="pointer-events-none absolute -inset-1 opacity-40"
        style={{ background: "radial-gradient(600px circle at 50% 0%, oklch(0.88 0.22 125 / 10%), transparent 60%)" }}
      />
      <div className="relative grid gap-5 lg:grid-cols-[minmax(0,1fr)_auto]">
        <div className="min-w-0 space-y-4">
          <div className="flex items-center gap-2">
            <StatusBadge tone="muted" dot>Idle · IVR</StatusBadge>
            <span className="text-mono text-[10px] text-white/40">no active session</span>
          </div>
          <div>
            <h2 className="font-display text-xl font-bold sm:text-2xl">
              <span aria-hidden>📞 </span>Waiting for incoming call…
            </h2>
            <p className="mt-1 max-w-lg text-sm text-white/55">
              No active IVR session. Live call telemetry, transcripts, and scheme
              recommendations appear here the moment a farmer dials in.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-1 text-[10px] text-mono uppercase tracking-widest text-white/40">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-1">
              <span className="size-1.5 rounded-full bg-white/40" />
              Waiting for backend connection
            </span>
          </div>
        </div>

        <div className="flex min-w-[240px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/10 bg-white/[0.015] p-6">
          <div className="relative grid size-16 place-items-center rounded-full bg-white/[0.03] ring-1 ring-white/10">
            <PhoneOff className="size-7 text-white/40" />
          </div>
          <VoiceWaveform tone="lime" className="w-full opacity-40" />
          <div className="text-mono text-[10px] uppercase tracking-widest text-white/40">
            Voice channel · idle
          </div>
        </div>
      </div>
    </section>
  );
}

function Chip({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
      <Icon className="size-3.5 shrink-0 text-[var(--lime-glow)]" />
      <div className="min-w-0">
        <div className="text-[9px] uppercase tracking-widest text-white/40">{label}</div>
        <div className="truncate text-xs font-semibold text-white/90">{value}</div>
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone }: { icon: React.ComponentType<{ className?: string }>; label: string; value: string; tone: "lime" | "sky" | "wheat" }) {
  const color =
    tone === "sky" ? "text-[var(--sky-agri)]" : tone === "wheat" ? "text-[var(--wheat)]" : "text-[var(--lime-glow)]";
  return (
    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">
      <Icon className={`size-3.5 ${color}`} />
      <span className="text-[10px] uppercase tracking-widest text-white/40">{label}</span>
      <span className={`text-mono text-xs font-semibold ${color}`}>{value}</span>
    </div>
  );
}
