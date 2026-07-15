import { Check, Loader2, Circle, ChevronDown } from "lucide-react";
import { GlassCard } from "@/components/layout/GlassCard";
import type { CallStage, MissionSnapshot } from "@/api/mission";
import { STAGES } from "@/api/mission";

type NodeState = "waiting" | "active" | "complete";

type WorkflowNode = {
  id: string;
  icon: string;
  label: string;
};

const NODES: WorkflowNode[] = [
  { id: "incoming-call", icon: "📞", label: "Incoming Call" },
  { id: "speech-recognition", icon: "🎙", label: "Speech Recognition" },
  { id: "farmer-identification", icon: "👤", label: "Farmer Identification" },
  { id: "digital-twin", icon: "🧠", label: "Digital Twin" },
  { id: "scheme-engine", icon: "🏛", label: "Government Scheme Engine" },
  { id: "eligibility", icon: "📑", label: "Eligibility Engine" },
  { id: "document-advisor", icon: "📄", label: "Document Advisor" },
  { id: "chief-reasoning", icon: "🧠", label: "Chief Reasoning Agent" },
  { id: "voice-response", icon: "🗣", label: "Voice Response" },
  { id: "call-complete", icon: "✅", label: "Call Complete" },
];

/**
 * Compute a state for every canvas node from the real MissionSnapshot only.
 * No timers, no random data — nodes remain "waiting" until backend events
 * populate the snapshot.
 */
function computeStates(snapshot: MissionSnapshot): Record<string, NodeState> {
  const { call, transcript, schemes, eligibility, thinking } = snapshot;
  const state: Record<string, NodeState> = Object.fromEntries(
    NODES.map((n) => [n.id, "waiting" as NodeState]),
  );

  if (!call) return state;

  const stageIdx = (id: CallStage) => STAGES.findIndex((s) => s.id === id);
  const cur = stageIdx(call.currentStage);
  const past = (id: CallStage) => cur > stageIdx(id);
  const at = (id: CallStage) => cur === stageIdx(id);

  // 1. Incoming call
  if (call.status === "ringing") state["incoming-call"] = "active";
  else state["incoming-call"] = "complete";

  // 2. Speech recognition — complete when we have transcript or moved past ASR
  if (past("speech-recognition") || transcript.length > 0) state["speech-recognition"] = "complete";
  else if (at("speech-recognition")) state["speech-recognition"] = "active";

  // 3. Farmer identification
  if (past("farmer-identification")) state["farmer-identification"] = "complete";
  else if (at("farmer-identification")) state["farmer-identification"] = "active";

  // 4. Digital twin
  if (past("digital-twin")) state["digital-twin"] = "complete";
  else if (at("digital-twin")) state["digital-twin"] = "active";

  // 5. Scheme engine
  if (past("scheme-search") || schemes.length > 0) state["scheme-engine"] = "complete";
  else if (at("scheme-search")) state["scheme-engine"] = "active";

  // 6. Eligibility
  if (past("eligibility") || eligibility.length > 0) state["eligibility"] = "complete";
  else if (at("eligibility")) state["eligibility"] = "active";

  // 7. Document advisor — tied to knowledge retrieval stage
  if (past("knowledge-retrieval")) state["document-advisor"] = "complete";
  else if (at("knowledge-retrieval")) state["document-advisor"] = "active";

  // 8. Chief reasoning
  if (past("reasoning")) state["chief-reasoning"] = "complete";
  else if (at("reasoning") || thinking) state["chief-reasoning"] = "active";

  // 9. Voice response
  if (past("voice-playback")) state["voice-response"] = "complete";
  else if (at("voice-playback") || at("response-generation")) state["voice-response"] = "active";

  // 10. Call complete
  if (call.status === "wrap-up") state["call-complete"] = "complete";

  return state;
}

export function WorkflowCanvas({ snapshot }: { snapshot: MissionSnapshot }) {
  const states = computeStates(snapshot);
  const anyActive = Object.values(states).some((s) => s !== "waiting");

  return (
    <GlassCard eyebrow="AI pipeline" title="Workflow Canvas" strong>
      <p className="mb-3 text-[11px] text-white/45">
        {anyActive
          ? "Reacting to live backend events"
          : "Awaiting backend events · every stage will animate independently as events arrive"}
      </p>

      {/* Desktop / tablet: horizontal flow */}
      <div className="hidden md:block">
        <div className="flex items-stretch gap-1 overflow-x-auto pb-2">
          {NODES.map((node, i) => (
            <div key={node.id} className="flex items-center">
              <WorkflowNodeCard node={node} state={states[node.id]} />
              {i < NODES.length - 1 && <Connector active={states[node.id] === "complete"} />}
            </div>
          ))}
        </div>
      </div>

      {/* Mobile: vertical flow */}
      <div className="md:hidden">
        <ol className="flex flex-col gap-2">
          {NODES.map((node, i) => (
            <li key={node.id} className="flex flex-col items-stretch">
              <WorkflowNodeCard node={node} state={states[node.id]} fullWidth />
              {i < NODES.length - 1 && (
                <div className="my-1 flex justify-center">
                  <ChevronDown
                    className={`size-4 transition-colors ${
                      states[node.id] === "complete" ? "text-[var(--lime-glow)]" : "text-white/20"
                    }`}
                  />
                </div>
              )}
            </li>
          ))}
        </ol>
      </div>
    </GlassCard>
  );
}

function WorkflowNodeCard({
  node,
  state,
  fullWidth = false,
}: {
  node: WorkflowNode;
  state: NodeState;
  fullWidth?: boolean;
}) {
  const base =
    "relative flex shrink-0 flex-col items-center gap-2 rounded-2xl border px-3 py-3 text-center transition-all";
  const width = fullWidth ? "w-full" : "min-w-[132px] max-w-[148px]";

  const skin =
    state === "active"
      ? "border-[var(--lime-glow)]/50 bg-[var(--lime-glow)]/[0.08] shadow-[0_0_24px_-8px_var(--lime-glow)]"
      : state === "complete"
        ? "border-emerald-400/30 bg-emerald-400/[0.05]"
        : "border-white/5 bg-white/[0.015]";

  const labelColor =
    state === "waiting" ? "text-white/40" : state === "active" ? "text-white" : "text-white/85";

  return (
    <div className={`${base} ${width} ${skin}`}>
      {state === "active" && (
        <span className="pointer-events-none absolute inset-0 rounded-2xl ring-1 ring-[var(--lime-glow)]/40 animate-pulse" />
      )}
      <div
        className={`grid size-10 place-items-center rounded-xl text-lg ring-1 ${
          state === "active"
            ? "bg-[var(--lime-glow)]/15 ring-[var(--lime-glow)]/40"
            : state === "complete"
              ? "bg-emerald-400/10 ring-emerald-400/30"
              : "bg-white/[0.03] ring-white/10 grayscale opacity-60"
        }`}
        aria-hidden
      >
        <span>{node.icon}</span>
      </div>
      <div className={`text-[11px] font-semibold leading-tight ${labelColor}`}>{node.label}</div>
      <StatusPill state={state} />
    </div>
  );
}

function StatusPill({ state }: { state: NodeState }) {
  if (state === "complete") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest text-emerald-300 ring-1 ring-emerald-400/30">
        <Check className="size-2.5" /> Done
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-[var(--lime-glow)]/15 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest text-[var(--lime-glow)] ring-1 ring-[var(--lime-glow)]/40">
        <Loader2 className="size-2.5 animate-spin" /> Active
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-white/[0.03] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-widest text-white/40 ring-1 ring-white/10">
      <Circle className="size-2" /> Waiting…
    </span>
  );
}

function Connector({ active }: { active: boolean }) {
  return (
    <div className="mx-0.5 flex h-1 w-6 items-center">
      <div
        className={`h-[2px] w-full rounded-full transition-all ${
          active
            ? "bg-gradient-to-r from-[var(--lime-glow)]/70 to-emerald-400/60 shadow-[0_0_8px_-1px_var(--lime-glow)]"
            : "bg-white/10"
        }`}
      />
    </div>
  );
}
