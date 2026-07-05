"use client";

import React from "react";
import { useDashboard } from "@/components/DashboardContext";
import { Brain, Layers, Clock, Zap, Shield, HelpCircle, Activity } from "lucide-react";

export default function RightThinkingPanel() {
  const {
    aiState,
    callActive,
    systemLogs,
    metrics,
    aiSummary
  } = useDashboard();

  const stages = [
    { key: "CALL_STARTED", label: "Call Ingress" },
    { key: "CALLER_IDENTIFIED", label: "Caller ID" },
    { key: "DIGITAL_TWIN_LOADED", label: "Digital Twin" },
    { key: "SCHEME_SEARCH_STARTED", label: "Scheme Search" },
    { key: "SCHEME_EVALUATING", label: "Evaluating" },
    { key: "REASONING_COMPLETED", label: "AI Reasoning" },
    { key: "DOCUMENT_ADVISOR_READY", label: "Docs Ready" },
    { key: "VOICE_RESPONSE", label: "Voice Playback" },
    { key: "CALL_COMPLETED", label: "Completed" }
  ];

  const getStageIndex = (state: string) => {
    if (state === "CALL_COMPLETED") return 8;
    if (state === "VOICE_RESPONSE") return 7;
    if (state === "DOCUMENT_ADVISOR_READY") return 6;
    if (state === "REASONING_COMPLETED") return 5;
    if (state === "ELIGIBILITY_COMPLETED") return 5;
    if (state === "SCHEME_EVALUATING") return 4;
    if (state === "SCHEME_SEARCH_STARTED") return 3;
    if (state === "DIGITAL_TWIN_LOADED") return 2;
    if (state === "CALLER_IDENTIFIED") return 1;
    if (state === "CALL_STARTED") return 0;
    return -1;
  };

  const activeIndex = getStageIndex(aiState);

  // Fallbacks for telemetry
  const avgLatency = metrics?.workflow_latency?.avg_ms ?? 145.2;
  const activeCost = aiSummary?.accumulated_cost_usd ?? 0.0;
  const interventions = metrics?.safety_interventions_count ?? 0;

  return (
    <aside className="w-80 bg-slate-950/20 border-l border-slate-900/60 p-5 flex flex-col gap-6 select-none shrink-0 h-[calc(100vh-53px)] overflow-y-auto mc-scrollbar">
      {/* 🧠 Live AI Thinking */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 border-b border-slate-900/60 pb-2">
          <Brain className="w-4.5 h-4.5 text-emerald-400 animate-pulse" />
          <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Live AI Thinking</span>
        </div>
        <div className="bg-slate-950/80 border border-slate-900/80 rounded-2xl p-3 h-48 overflow-y-auto mc-scrollbar font-mono text-[9px] text-slate-400 leading-relaxed flex flex-col gap-2">
          {systemLogs.length === 0 ? (
            <span className="text-slate-650 italic">Telemetry listening. System idle...</span>
          ) : (
            systemLogs.slice(0, 15).map((log, i) => (
              <div key={i} className="border-b border-slate-900/40 pb-1 last:border-0">
                {log}
              </div>
            ))
          )}
        </div>
      </div>

      {/* 🧭 Workflow Progress */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 border-b border-slate-900/60 pb-2">
          <Layers className="w-4.5 h-4.5 text-sky-400" />
          <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Workflow Progress</span>
        </div>
        {callActive ? (
          <div className="flex flex-col gap-1.5 pl-2 relative border-l border-slate-900">
            {stages.map((st, idx) => {
              const isPassed = idx < activeIndex;
              const isActive = idx === activeIndex;

              let dotColor = "bg-slate-800 border-slate-900 text-slate-600";
              let labelColor = "text-slate-500 font-normal";

              if (isPassed) {
                dotColor = "bg-emerald-500/20 border-emerald-500/40 text-emerald-400";
                labelColor = "text-slate-300 font-semibold";
              } else if (isActive) {
                dotColor = "bg-sky-500/30 border-sky-500/60 text-sky-400 shadow-md shadow-sky-500/10";
                labelColor = "text-sky-400 font-bold animate-pulse";
              }

              return (
                <div key={st.key} className="flex items-center gap-3 relative py-0.5">
                  {/* Step Dot */}
                  <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[8px] font-black border transition-all ${dotColor}`}>
                    {isPassed ? "✓" : idx + 1}
                  </div>
                  {/* Step Label */}
                  <span className={`text-[10px] uppercase tracking-wider ${labelColor}`}>{st.label}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="border border-dashed border-slate-900 rounded-2xl p-6 text-center text-slate-600 text-[10px] italic">
            No active simulated call session. Select a farmer under Mission Control to start.
          </div>
        )}
      </div>

      {/* 📊 Quick Telemetry */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2 border-b border-slate-900/60 pb-2">
          <Activity className="w-4.5 h-4.5 text-indigo-400" />
          <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Quick Telemetry</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-slate-900/30 border border-slate-900/60 p-3 rounded-2xl text-center">
            <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Avg Latency</span>
            <span className="text-sm font-black text-sky-400 font-mono block mt-1">{avgLatency.toFixed(0)}ms</span>
          </div>
          <div className="bg-slate-900/30 border border-slate-900/60 p-3 rounded-2xl text-center">
            <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Accumulated Cost</span>
            <span className="text-sm font-black text-emerald-400 font-mono block mt-1">${activeCost.toFixed(3)}</span>
          </div>
          <div className="bg-slate-900/30 border border-slate-900/60 p-3 rounded-2xl text-center col-span-2">
            <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Safety Interventions</span>
            <span className="text-sm font-black text-amber-500 font-mono block mt-1">{interventions}</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
