import { Bot } from "lucide-react";

export function AgentGrid() {
  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-6">
      <div className="mb-5 flex items-end justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--lime-glow)]">
            Neural Fleet
          </div>
          <h2 className="mt-1 font-display text-xl font-bold sm:text-2xl">AI Agent Command</h2>
        </div>
      </div>
      <div className="grid place-items-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02] p-10 text-center">
        <div className="grid size-12 place-items-center rounded-2xl bg-white/5 text-white/50">
          <Bot className="size-5" />
        </div>
        <div className="mt-3 text-sm font-semibold text-white/85">No active AI agents</div>
        <div className="mt-1 max-w-xs text-xs text-white/50">
          Waiting for backend — agent health, confidence, latency, and load will appear here once telemetry streams in.
        </div>
      </div>
    </div>
  );
}
