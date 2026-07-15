import { User, MapPin, Sprout, Ruler, Languages, Clock, Sparkles, ShieldCheck, UserSearch } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import type { LiveCall } from "@/api/mission";

export function FarmerTwin({ farmer }: { farmer: LiveCall["farmer"] | null }) {
  if (!farmer) {
    return (
      <GlassCard eyebrow="Digital Twin" title="Farmer Profile" strong>
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-8 text-center">
          <UserSearch className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">No farmer identified yet.</div>
          <div className="text-[11px] text-white/40">The digital twin loads when an incoming call is matched.</div>
        </div>
      </GlassCard>
    );
  }

  const rows: [React.ComponentType<{ className?: string }>, string, string][] = [
    [MapPin, "Village · District", `${farmer.village} · ${farmer.district}`],
    [MapPin, "State", farmer.state],
    [Sprout, "Primary crop", farmer.crop],
    [Ruler, "Farm size", `${farmer.landHa} ha · ${farmer.category}`],
    [Languages, "Preferred language", farmer.language],
    [ShieldCheck, "Aadhaar", farmer.aadhaarMasked],
    [Clock, "Last interaction", farmer.lastInteraction],
  ];

  return (
    <GlassCard eyebrow="Digital Twin · loaded" title="Farmer Profile" strong>
      <div className="flex items-center gap-4">
        <div className="relative grid size-16 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-[var(--lime-glow)]/25 to-[var(--forest-800)]/40 font-display text-xl font-bold ring-1 ring-[var(--lime-glow)]/30">
          {farmer.avatarInitials}
          <span className="absolute -bottom-1 -right-1 grid size-5 place-items-center rounded-full bg-emerald-400 text-[var(--forest-950)] ring-2 ring-[var(--forest-950)]">
            <User className="size-2.5" />
          </span>
        </div>
        <div className="min-w-0">
          <div className="truncate font-display text-base font-bold">{farmer.name}</div>
          <div className="text-mono text-[11px] text-white/50">{farmer.phone}</div>
          <div className="mt-1.5 inline-flex items-center gap-1.5 rounded-full bg-[var(--lime-glow)]/15 px-2 py-0.5 text-[10px] text-[var(--lime-glow)] ring-1 ring-[var(--lime-glow)]/30">
            <Sparkles className="size-3" /> Twin confidence {Math.round(farmer.twinConfidence * 100)}%
          </div>
        </div>
      </div>

      <dl className="mt-4 grid gap-1.5">
        {rows.map(([Icon, k, v]) => (
          <div key={k} className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-2.5 py-1.5">
            <Icon className="size-3.5 shrink-0 text-[var(--lime-glow)]" />
            <dt className="text-[10px] uppercase tracking-widest text-white/40">{k}</dt>
            <dd className="ml-auto truncate text-[11px] font-semibold text-white/85">{v}</dd>
          </div>
        ))}
      </dl>

      {farmer.previousScheme && (
        <div className="mt-3 rounded-xl border border-[var(--wheat)]/20 bg-[var(--wheat)]/[0.05] p-2.5 text-[11px] text-white/75">
          <div className="text-[9px] uppercase tracking-widest text-[var(--wheat)]">Previous recommendation</div>
          <div className="mt-0.5">{farmer.previousScheme}</div>
        </div>
      )}
    </GlassCard>
  );
}
