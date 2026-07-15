import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { BookOpen, Sparkles, ExternalLink } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { SearchInput } from "@/components/layout/SearchInput";
import { FilterChips } from "@/components/layout/FilterChips";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { knowledgeApi, type KnowledgeCard } from "@/api/knowledge";

export const Route = createFileRoute("/knowledge")({
  head: () => ({ meta: [{ title: "Knowledge Base · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const [q, setQ] = useState("");
  const [cat, setCat] = useState<string | null>(null);
  const cards = useResource(
    () => knowledgeApi.list(q, cat as KnowledgeCard["category"] | undefined),
    [q, cat],
  );

  return (
    <AppShell>
      <PageHeader
        icon={BookOpen}
        eyebrow="RAG corpus"
        title="Knowledge Base"
        description="Grounded corpus powering AI agents — protocols, research papers, gazette notifications, and vernacular guides."
      />

      <StatGrid stats={[
        { label: "Documents", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "Chunks indexed", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "Retrieval hit@5", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Freshness", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <GlassCard eyebrow="Search" title="Ask the knowledge base" strong>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex-1">
            <SearchInput value={q} onChange={setQ} placeholder='e.g. "pink bollworm control in Vidarbha"' />
          </div>
          <button className="inline-flex items-center gap-1.5 rounded-full bg-[var(--lime-glow)] px-4 py-1.5 text-xs font-bold text-[var(--forest-950)]">
            <Sparkles className="size-3" /> Ask AI
          </button>
        </div>
        <div className="mt-3">
          <FilterChips
            options={[
              { value: "Advisory", label: "Advisory" },
              { value: "Circular", label: "Circular" },
              { value: "Best practice", label: "Best practice" },
              { value: "Research", label: "Research" },
            ]}
            value={cat}
            onChange={setCat}
          />
        </div>
      </GlassCard>

      <StateWrapper state={cards} emptyTitle="No matching articles">
        {(rows) => (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {rows.map((c) => (
              <article key={c.id} className="glass-panel-strong flex flex-col rounded-2xl border border-white/5 p-5 transition hover:border-[var(--lime-glow)]/30">
                <div className="flex items-center justify-between">
                  <StatusBadge tone={c.category === "Advisory" ? "lime" : c.category === "Circular" ? "sky" : c.category === "Research" ? "wheat" : "leaf"}>{c.category}</StatusBadge>
                  {c.crop && <span className="text-[10px] text-mono text-white/40">{c.crop}</span>}
                </div>
                <h3 className="mt-2 font-display text-sm font-bold leading-snug">{c.title}</h3>
                <p className="mt-2 flex-1 text-xs text-white/60">{c.excerpt}</p>
                <div className="mt-3 flex items-center justify-between text-[10px] text-mono text-white/40">
                  <span>{c.source} · {c.updatedAt}</span>
                  <ExternalLink className="size-3 text-[var(--lime-glow)]" />
                </div>
              </article>
            ))}
          </div>
        )}
      </StateWrapper>
    </AppShell>
  );
}
