import type { ReactNode } from "react";

export type TimelineItem = {
  at: string;
  kind: string;
  text: ReactNode;
  tone?: "lime" | "sky" | "wheat" | "red" | "muted";
};

const toneMap: Record<string, string> = {
  lime: "bg-[var(--lime-glow)]",
  sky: "bg-[var(--sky-agri)]",
  wheat: "bg-[var(--wheat)]",
  red: "bg-red-400",
  muted: "bg-white/30",
};

export function Timeline({ items }: { items: TimelineItem[] }) {
  return (
    <ol className="relative space-y-4 border-l border-white/10 pl-4">
      {items.map((it, i) => (
        <li key={i} className="relative">
          <span
            className={`absolute -left-[21px] top-1.5 size-2.5 rounded-full ring-4 ring-[var(--forest-900)] ${toneMap[it.tone ?? "lime"]}`}
          />
          <div className="flex items-baseline gap-2 text-[10px] text-mono uppercase tracking-widest text-white/40">
            <span>{it.at}</span>
            <span className="text-[var(--lime-glow)]/70">· {it.kind}</span>
          </div>
          <div className="mt-1 text-sm text-white/80">{it.text}</div>
        </li>
      ))}
    </ol>
  );
}
