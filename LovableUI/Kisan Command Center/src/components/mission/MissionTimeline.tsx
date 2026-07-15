import { Radio } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import { Timeline, type TimelineItem } from "@/components/layout/Timeline";
import { STAGES, type CallStage, type TimelineEntry } from "@/api/mission";

export function MissionTimeline({
  entries,
  currentStage,
}: {
  entries: TimelineEntry[];
  currentStage: CallStage | null;
}) {
  if (entries.length === 0) {
    return (
      <GlassCard eyebrow="Session log" title="AI Timeline" strong>
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 p-8 text-center">
          <Radio className="size-6 text-white/30" />
          <div className="text-sm font-semibold text-white/70">No session events yet.</div>
          <div className="text-[11px] text-white/40">Stage transitions will be logged as they arrive.</div>
        </div>
      </GlassCard>
    );
  }

  const items: TimelineItem[] = entries.map((e) => {
    const stage = STAGES.find((s) => s.id === e.stage);
    return {
      at: e.at,
      kind: stage?.hint ?? e.stage,
      text: stage?.label ?? e.stage,
      tone: e.stage === currentStage ? "lime" : "sky",
    };
  });

  return (
    <GlassCard eyebrow="Session log" title="AI Timeline" strong>
      <Timeline items={items} />
    </GlassCard>
  );
}
