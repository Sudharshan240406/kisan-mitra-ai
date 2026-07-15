import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { MessageSquare, Sparkles, PhoneCall, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatGrid } from "@/components/layout/StatGrid";
import { GlassCard } from "@/components/layout/GlassCard";
import { StatusBadge } from "@/components/layout/StatusBadge";
import { SearchInput } from "@/components/layout/SearchInput";
import { StateWrapper } from "@/components/layout/StateWrapper";
import { useResource } from "@/hooks/useResource";
import { conversationsApi, type Conversation } from "@/api/conversations";

export const Route = createFileRoute("/conversations")({
  head: () => ({ meta: [{ title: "Conversations · Kisan Mitra" }] }),
  component: Page,
});

function Page() {
  const list = useResource(() => conversationsApi.list(), []);
  const [q, setQ] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);

  return (
    <AppShell>
      <PageHeader
        icon={MessageSquare}
        eyebrow="Inbox"
        title="Conversations"
        description="Omni-channel inbox — WhatsApp, IVR, SMS and app chat unified with AI drafting and human handoff."
      />

      <StatGrid stats={[
        { label: "Open threads", value: "—", delta: "Waiting for backend", tone: "lime" },
        { label: "Avg response", value: "—", delta: "Waiting for backend", tone: "sky" },
        { label: "CSAT · 7d", value: "—", delta: "Waiting for backend", tone: "wheat" },
        { label: "Languages", value: "—", delta: "Waiting for backend", tone: "leaf" },
      ]} />

      <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
        <GlassCard title="Live threads" eyebrow="Realtime" strong>
          <div className="mb-3">
            <SearchInput value={q} onChange={setQ} placeholder="Search conversations" />
          </div>
          <StateWrapper state={list}>
            {(rows) => {
              const filtered = rows.filter((r) => !q || `${r.farmer} ${r.intent}`.toLowerCase().includes(q.toLowerCase()));
              const active = filtered.find((r) => r.id === activeId) ?? filtered[0];
              return (
                <>
                  <div className="space-y-2">
                    {filtered.map((t) => {
                      const isActive = active?.id === t.id;
                      return (
                        <button
                          key={t.id}
                          onClick={() => setActiveId(t.id)}
                          className={`flex w-full items-start gap-3 rounded-xl p-3 text-left ring-1 ring-inset transition ${isActive ? "bg-[var(--lime-glow)]/10 ring-[var(--lime-glow)]/25" : "ring-white/5 hover:bg-white/[0.04]"}`}
                        >
                          <div className="grid size-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[var(--wheat)] to-[var(--earth)] text-[11px] font-bold text-[var(--forest-950)]">
                            {t.farmer.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate text-sm font-semibold">{t.farmer}</span>
                              <span className="text-[10px] text-mono text-white/40">{t.startedAt.slice(11)}</span>
                            </div>
                            <div className="truncate text-xs text-white/60">{t.intent}</div>
                            <div className="mt-1.5 flex items-center gap-2">
                              <StatusBadge tone={t.channel === "IVR" ? "sky" : t.channel === "WhatsApp" ? "lime" : "wheat"}>{t.channel}</StatusBadge>
                              <span className="text-[10px] text-mono text-white/40">{t.language}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                  <input type="hidden" data-active={active?.id} />
                </>
              );
            }}
          </StateWrapper>
        </GlassCard>

        <ThreadDetail list={list} activeId={activeId} />
      </div>
    </AppShell>
  );
}

function ThreadDetail({ list, activeId }: { list: ReturnType<typeof useResource<Conversation[]>>; activeId: string | null }) {
  const rows = list.data ?? [];
  const active = rows.find((r) => r.id === activeId) ?? rows[0];
  if (!active) {
    return <GlassCard title="Select a conversation" eyebrow="Thread" strong><div className="py-12 text-center text-sm text-white/40">No thread selected.</div></GlassCard>;
  }
  const sentimentTone = active.sentiment === "positive" ? "lime" : active.sentiment === "negative" ? "red" : "sky";
  return (
    <GlassCard title={`${active.farmer} · ${active.intent}`} eyebrow={`${active.channel} · ${active.language}`} strong
      actions={<StatusBadge tone={sentimentTone as any} dot>{active.sentiment}</StatusBadge>}>
      <div className="grid gap-3 sm:grid-cols-4">
        <MiniStat label="Duration" value={`${Math.floor(active.durationSec / 60)}m ${active.durationSec % 60}s`} />
        <MiniStat label="Confidence" value={`${(active.confidence * 100).toFixed(0)}%`} tone="lime" />
        <MiniStat label="Channel" value={active.channel} tone="sky" />
        <MiniStat label="Started" value={active.startedAt.slice(11)} />
      </div>

      <div className="mt-5 rounded-2xl bg-white/[0.03] p-4 ring-1 ring-inset ring-white/5">
        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
          <Sparkles className="size-3" /> AI Summary
        </div>
        <p className="text-sm text-white/85">{active.summary}</p>
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">
          <ShieldCheck className="size-3" /> Evidence & citations
        </div>
        <ul className="space-y-1.5">
          {active.evidence.map((e, i) => (
            <li key={i} className="rounded-lg bg-white/[0.03] px-3 py-2 text-xs text-white/70 ring-1 ring-inset ring-white/5">· {e}</li>
          ))}
        </ul>
      </div>

      <div className="mt-4 flex items-center gap-2 rounded-2xl bg-white/5 p-2 ring-1 ring-inset ring-white/10">
        <input placeholder="Type a reply · AI-assisted" className="flex-1 bg-transparent px-2 text-sm outline-none placeholder:text-white/40" />
        <button className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-white/80 ring-1 ring-inset ring-white/10 hover:bg-white/15">
          <PhoneCall className="size-3" /> Call
        </button>
        <button className="rounded-full bg-[var(--lime-glow)] px-3 py-1.5 text-[11px] font-bold text-[var(--forest-950)]">Send</button>
      </div>
    </GlassCard>
  );
}

function MiniStat({ label, value, tone = "white" }: { label: string; value: string; tone?: "white" | "lime" | "sky" }) {
  const t = tone === "lime" ? "text-[var(--lime-glow)]" : tone === "sky" ? "text-[var(--sky-agri)]" : "text-white";
  return (
    <div className="rounded-xl bg-white/[0.03] p-3 ring-1 ring-inset ring-white/5">
      <div className="text-[10px] text-mono uppercase text-white/40">{label}</div>
      <div className={`mt-0.5 text-sm font-bold ${t}`}>{value}</div>
    </div>
  );
}
