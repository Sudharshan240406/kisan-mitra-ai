import { FileCheck2, FileX2, FileText } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import type { SchemeRecommendation } from "@/api/mission";

export function DocumentAdvisor({ schemes }: { schemes: SchemeRecommendation[] }) {
  if (schemes.length === 0) {
    return (
      <GlassCard eyebrow="Document Advisor" title="Application Kit" strong>
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-8 text-center">
          <FileText className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">No documents to review yet.</div>
          <div className="text-[11px] text-white/40">A checklist will appear once schemes are recommended.</div>
        </div>
      </GlassCard>
    );
  }

  const seen = new Map<string, "have" | "missing">();
  for (const s of schemes) {
    for (const d of s.documents) {
      // "missing" wins so the farmer sees the strictest requirement.
      if (!seen.has(d.name) || d.status === "missing") seen.set(d.name, d.status);
    }
  }
  const docs = Array.from(seen, ([name, status]) => ({ name, status }));

  return (
    <GlassCard eyebrow="Document Advisor" title="Application Kit" strong>
      <div className="text-[10px] uppercase tracking-widest text-white/40">Required documents</div>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {docs.map((d) => {
          const missing = d.status === "missing";
          return (
            <li
              key={d.name}
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] ring-1 ring-inset ${
                missing
                  ? "bg-red-500/10 text-red-200 ring-red-400/25"
                  : "bg-emerald-400/10 text-emerald-200 ring-emerald-400/25"
              }`}
            >
              {missing ? <FileX2 className="size-3" /> : <FileCheck2 className="size-3" />}
              {d.name}
              <span className="text-mono text-[9px] opacity-70">· {missing ? "MISSING" : "ON FILE"}</span>
            </li>
          );
        })}
      </ul>
    </GlassCard>
  );
}
