import { useEffect, useRef } from "react";
import { Bot, User, MessageSquareOff } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import type { TranscriptLine } from "@/api/mission";

export function TranscriptPanel({ lines, thinking }: { lines: TranscriptLine[]; thinking: boolean }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [lines.length, thinking]);

  const hasLines = lines.length > 0;

  return (
    <GlassCard
      eyebrow="Realtime ASR · streaming"
      title="Live Transcript"
      strong
      actions={
        <span className="flex items-center gap-1.5 text-[10px] text-mono text-white/50">
          <span className={`size-1.5 rounded-full ${hasLines ? "bg-[var(--lime-glow)] animate-pulse-soft" : "bg-white/30"}`} />
          {hasLines ? "Streaming" : "Idle"}
        </span>
      }
    >
      <div ref={scrollRef} className="max-h-[380px] space-y-3 overflow-y-auto pr-1">
        {!hasLines && !thinking && (
          <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-10 text-center">
            <MessageSquareOff className="size-6 text-white/30" />
            <div className="text-sm font-semibold text-white/70">No active conversation.</div>
            <div className="text-[11px] text-white/40">Transcripts will appear line by line as the farmer speaks.</div>
          </div>
        )}
        {lines.map((l) => (
          <TranscriptBubble key={l.id} line={l} />
        ))}
        {thinking && (
          <div className="flex items-center gap-2 pl-10 text-[11px] text-white/50">
            <div className="flex gap-1">
              <Dot delay={0} /><Dot delay={0.15} /><Dot delay={0.3} />
            </div>
            <span className="text-mono uppercase tracking-widest">AI is thinking…</span>
          </div>
        )}
      </div>
    </GlassCard>
  );
}

function TranscriptBubble({ line }: { line: TranscriptLine }) {
  const isAi = line.speaker === "ai";
  return (
    <div className={`flex items-start gap-2 ${isAi ? "" : "flex-row-reverse"} animate-fade-in`}>
      <div
        className={`grid size-7 shrink-0 place-items-center rounded-full ring-1 ring-inset ${
          isAi
            ? "bg-[var(--lime-glow)]/15 text-[var(--lime-glow)] ring-[var(--lime-glow)]/30"
            : "bg-[var(--sky-agri)]/15 text-[var(--sky-agri)] ring-[var(--sky-agri)]/30"
        }`}
      >
        {isAi ? <Bot className="size-3.5" /> : <User className="size-3.5" />}
      </div>
      <div className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm ring-1 ring-inset ${
        isAi
          ? "bg-gradient-to-br from-[var(--forest-800)]/40 to-[var(--forest-900)]/40 ring-[var(--lime-glow)]/15 text-white/90"
          : "bg-white/[0.04] ring-white/10 text-white/80"
      }`}>
        <div className="mb-0.5 flex items-center gap-2 text-[9px] uppercase tracking-widest text-white/40">
          <span>{isAi ? "AI · Kisan Mitra" : "Farmer"}</span>
          {line.lang && <span className="text-[var(--lime-glow)]/70">· {line.lang}</span>}
          <span className="text-mono">{line.at}</span>
        </div>
        <div className="leading-snug">{line.text}</div>
      </div>
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <span
      className="inline-block size-1.5 rounded-full bg-[var(--lime-glow)]"
      style={{ animation: "pulse-soft 1.2s ease-in-out infinite", animationDelay: `${delay}s` }}
    />
  );
}
