import { Landmark, Sparkles, FileCheck2, FileX2, Phone, ArrowRight, Check, AlertTriangle } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import type { SchemeRecommendation, EligibilityCheck } from "@/api/mission";

export function SchemesPanel({ schemes }: { schemes: SchemeRecommendation[] }) {
  const hasSchemes = schemes.length > 0;
  return (
    <GlassCard
      eyebrow="AI Recommendations · ranked by confidence"
      title="Government Schemes"
      strong
      actions={
        <StatusBadge tone={hasSchemes ? "lime" : "muted"} dot={hasSchemes}>
          {hasSchemes ? "Live match" : "Idle"}
        </StatusBadge>
      }
    >
      {!hasSchemes ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-10 text-center">
          <Landmark className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">No recommendations yet.</div>
          <div className="text-[11px] text-white/40">Matching schemes appear once the AI has understood the farmer's need.</div>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {schemes.map((s) => (
            <SchemeCard key={s.id} scheme={s} />
          ))}
        </div>
      )}
    </GlassCard>
  );
}

function SchemeCard({ scheme }: { scheme: SchemeRecommendation }) {
  const tone: "lime" | "wheat" | "sky" =
    scheme.eligibility === "Eligible" ? "lime" : scheme.eligibility === "Likely" ? "wheat" : "sky";

  return (
    <article className="group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-[var(--forest-900)]/60 to-[var(--forest-950)]/40 p-4 transition hover:border-[var(--lime-glow)]/30 hover:shadow-[0_0_30px_-10px_var(--lime-glow)]">
      <div className="pointer-events-none absolute -right-8 -top-8 size-32 rounded-full bg-[var(--lime-glow)]/[0.06] blur-2xl" />
      <div className="relative">
        <div className="flex items-start justify-between gap-2">
          <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-[var(--lime-glow)]/15 ring-1 ring-[var(--lime-glow)]/30">
            <Landmark className="size-4 text-[var(--lime-glow)]" />
          </div>
          <StatusBadge tone={tone} dot>{scheme.eligibility}</StatusBadge>
        </div>

        <h4 className="mt-3 line-clamp-2 font-display text-sm font-bold leading-tight">{scheme.name}</h4>
        <div className="mt-0.5 text-[10px] text-mono text-white/40">{scheme.department}</div>

        {/* Confidence */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-[10px] text-mono text-white/50">
            <span className="flex items-center gap-1"><Sparkles className="size-3 text-[var(--lime-glow)]" /> AI confidence</span>
            <span className="text-[var(--lime-glow)]">{Math.round(scheme.confidence * 100)}%</span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[var(--lime-glow)] to-emerald-300 transition-all"
              style={{ width: `${scheme.confidence * 100}%` }}
            />
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-white/5 bg-white/[0.02] p-2.5 text-[11px] text-white/70">
          <div className="text-[9px] uppercase tracking-widest text-white/40">Benefit</div>
          <div className="mt-0.5">{scheme.benefit}</div>
        </div>

        <div className="mt-3">
          <div className="text-[9px] uppercase tracking-widest text-white/40">Documents</div>
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {scheme.documents.map((d) => (
              <li
                key={d.name}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] ring-1 ring-inset ${
                  d.status === "have"
                    ? "bg-emerald-400/10 text-emerald-300 ring-emerald-400/25"
                    : "bg-red-500/10 text-red-300 ring-red-400/25"
                }`}
              >
                {d.status === "have" ? <FileCheck2 className="size-3" /> : <FileX2 className="size-3" />}
                {d.name}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] text-mono text-white/50">
          <div className="rounded-lg border border-white/5 bg-white/[0.02] px-2 py-1">
            <div className="text-[9px] uppercase tracking-widest text-white/40">Deadline</div>
            <div className="mt-0.5 text-[11px] text-white/80">{scheme.deadline}</div>
          </div>
          <div className="rounded-lg border border-white/5 bg-white/[0.02] px-2 py-1">
            <div className="text-[9px] uppercase tracking-widest text-white/40">Helpline</div>
            <div className="mt-0.5 flex items-center gap-1 text-[11px] text-[var(--sky-agri)]"><Phone className="size-3" />{scheme.helpline}</div>
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-[var(--lime-glow)]/20 bg-[var(--lime-glow)]/[0.04] p-2.5 text-[11px] leading-snug text-white/75">
          <div className="mb-0.5 text-[9px] uppercase tracking-widest text-[var(--lime-glow)]">Why recommended</div>
          {scheme.why}
        </div>

        <button
          type="button"
          className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[var(--lime-glow)] to-emerald-300 px-3 py-2 text-xs font-bold text-[var(--forest-950)] shadow-[0_0_20px_-6px_var(--lime-glow)] transition hover:brightness-110"
        >
          Assist farmer to apply <ArrowRight className="size-3.5" />
        </button>
      </div>
    </article>
  );
}

export function EligibilityPanel({ checks }: { checks: EligibilityCheck[] }) {
  const passed = checks.filter((c) => c.status === "pass").length;
  const hasChecks = checks.length > 0;
  return (
    <GlassCard
      eyebrow="Rule engine · Chief agent"
      title="Eligibility Analysis"
      strong
      actions={
        hasChecks ? (
          <span className="text-mono text-[11px] text-[var(--lime-glow)]">{passed}/{checks.length} verified</span>
        ) : null
      }
    >
      {!hasChecks ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-6 text-center">
          <Check className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">Waiting for farmer identification.</div>
          <div className="text-[11px] text-white/40">Rule evaluations appear once a farmer is matched and schemes are scored.</div>
        </div>
      ) : (
        <ul className="space-y-2">
          {checks.map((c, i) => (
            <li
              key={c.label}
              className="flex items-start gap-3 rounded-xl border border-white/5 bg-white/[0.02] p-2.5"
              style={{ animation: "fade-in 0.4s ease-out both", animationDelay: `${i * 60}ms` }}
            >
              <StageDot status={c.status} />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold text-white/90">{c.label}</div>
                <div className="text-[11px] text-white/50">{c.detail}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </GlassCard>
  );
}

function StageDot({ status }: { status: EligibilityCheck["status"] }) {
  if (status === "pass")
    return (
      <span className="grid size-6 shrink-0 place-items-center rounded-full bg-emerald-400/15 ring-1 ring-emerald-400/40">
        <Check className="size-3.5 text-emerald-300" />
      </span>
    );
  if (status === "warn")
    return (
      <span className="grid size-6 shrink-0 place-items-center rounded-full bg-[var(--wheat)]/15 ring-1 ring-[var(--wheat)]/40">
        <AlertTriangle className="size-3.5 text-[var(--wheat)]" />
      </span>
    );
  return (
    <span className="grid size-6 shrink-0 place-items-center rounded-full bg-red-500/15 ring-1 ring-red-400/40">
      <AlertTriangle className="size-3.5 text-red-300" />
    </span>
  );
}
