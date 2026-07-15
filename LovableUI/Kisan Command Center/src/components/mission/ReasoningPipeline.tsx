import { Check, Loader2, Circle } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import { STAGES, type CallStage } from "@/api/mission";

export function ReasoningPipeline({ current }: { current: CallStage | null }) {
  const currentIdx = current ? STAGES.findIndex((s) => s.id === current) : -1;

  return (
    <GlassCard eyebrow="Neural pipeline" title="AI Reasoning" strong>
      {!current && (
        <div className="mb-3 rounded-xl border border-dashed border-white/10 p-3 text-center text-[11px] text-white/50">
          Pipeline idle · no reasoning in progress
        </div>
      )}
      <ol className="grid gap-2.5">
        {STAGES.map((s, i) => {
          const state = i < currentIdx ? "done" : i === currentIdx ? "active" : "pending";
          return (
            <li
              key={s.id}
              className={`group flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-all ${
                state === "active"
                  ? "border-[var(--lime-glow)]/40 bg-[var(--lime-glow)]/[0.06] shadow-[0_0_20px_-8px_var(--lime-glow)]"
                  : state === "done"
                    ? "border-white/10 bg-white/[0.02]"
                    : "border-white/5 bg-transparent"
              }`}
            >
              <span className="text-mono w-5 text-[10px] text-white/40">{String(i + 1).padStart(2, "0")}</span>
              <StageIcon state={state} />
              <div className="min-w-0 flex-1">
                <div className={`truncate text-sm font-semibold ${state === "pending" ? "text-white/40" : "text-white/90"}`}>
                  {s.label}
                </div>
                <div className="truncate text-[10px] text-mono text-white/40">{s.hint}</div>
              </div>
              {state === "active" && (
                <span className="text-[10px] text-mono uppercase tracking-widest text-[var(--lime-glow)]">Running</span>
              )}
              {state === "done" && (
                <span className="text-[10px] text-mono uppercase tracking-widest text-emerald-300/80">Done</span>
              )}
            </li>
          );
        })}
      </ol>
    </GlassCard>
  );
}

function StageIcon({ state }: { state: "done" | "active" | "pending" }) {
  if (state === "done")
    return (
      <span className="grid size-6 place-items-center rounded-full bg-emerald-400/15 ring-1 ring-emerald-400/40">
        <Check className="size-3.5 text-emerald-300" />
      </span>
    );
  if (state === "active")
    return (
      <span className="grid size-6 place-items-center rounded-full bg-[var(--lime-glow)]/15 ring-1 ring-[var(--lime-glow)]/50">
        <Loader2 className="size-3.5 animate-spin text-[var(--lime-glow)]" />
      </span>
    );
  return (
    <span className="grid size-6 place-items-center rounded-full ring-1 ring-white/10">
      <Circle className="size-3 text-white/30" />
    </span>
  );
}
