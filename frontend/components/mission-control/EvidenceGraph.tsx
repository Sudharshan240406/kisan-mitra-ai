"use client";

import React from "react";
import { ShieldCheck, BookOpen, CloudSun, Database } from "lucide-react";

export interface EvidenceItem {
  id?: string;
  agent?: string;
  source?: string;
  confidence?: number;
  weight?: number;
  reasoning?: string;
  text?: string;
}

export interface EvidenceGraphProps {
  evidence: (string | EvidenceItem)[];
  overallConfidence?: number;
}

export function EvidenceGraph({ evidence, overallConfidence = 0.92 }: EvidenceGraphProps) {
  return (
    <div className="glass-panel border border-slate-900 rounded-3xl p-5 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-900 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
            Multi-Agent Evidence Framework
          </h4>
        </div>
        <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
          {(overallConfidence * 100).toFixed(0)}% Consensus
        </span>
      </div>

      <div className="space-y-2">
        {evidence.length === 0 ? (
          <div className="text-[10px] text-slate-600 italic py-6 text-center font-mono">
            No agent evidence items collected for current state.
          </div>
        ) : (
          evidence.map((item, idx) => {
            const isString = typeof item === "string";
            const title = isString ? item : `${item.agent || item.source || "Agent"} Evidence`;
            const reasoning = isString ? item : item.reasoning || item.text || "";
            const confidencePct = !isString && item.confidence ? (item.confidence * 100).toFixed(0) : "90";

            return (
              <div key={idx} className="p-3 bg-slate-950/60 border border-slate-900 rounded-2xl space-y-1.5 font-mono text-[10.5px]">
                <div className="flex justify-between items-center text-[9.5px]">
                  <span className="text-emerald-400 font-bold uppercase flex items-center gap-1.5">
                    <Database className="w-3 h-3 text-slate-500" />
                    {title}
                  </span>
                  <span className="text-slate-500">{confidencePct}% confidence</span>
                </div>
                <p className="text-slate-300 text-[10px] font-sans leading-relaxed">{reasoning}</p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
