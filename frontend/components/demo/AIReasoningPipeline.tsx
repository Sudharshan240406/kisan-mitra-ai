"use client";

import React, { memo } from "react";
import { motion } from "framer-motion";
import { Mic, Server, BookOpen, Cpu, Volume2, CheckCircle2, Zap } from "lucide-react";

interface AIReasoningPipelineProps {
  activeStep: number; // 0: Idle, 1: STT, 2: Digital Twin, 3: RAG & Rules, 4: AI Reasoning, 5: Voice Output
}

const PIPELINE_STEPS = [
  { step: 1, label: "Speech STT",    icon: Mic,      desc: "Audio Ingestion & STT"          },
  { step: 2, label: "Digital Twin",  icon: Server,   desc: "Land & Farmer Context"          },
  { step: 3, label: "Scheme RAG",    icon: BookOpen, desc: "Eligibility Rules Engine"       },
  { step: 4, label: "AI Reasoning",  icon: Cpu,      desc: "LangGraph Verification"         },
  { step: 5, label: "Voice Output",  icon: Volume2,  desc: "Multilingual TTS Synthesis"     },
];

function AIReasoningPipelineInner({ activeStep }: AIReasoningPipelineProps) {
  const isProcessing = activeStep > 0 && activeStep < 5;
  const isSpeaking = activeStep === 5;

  return (
    <div className="my-3 rounded-2xl border border-slate-800/80 bg-slate-900/80 p-3.5 backdrop-blur-md overflow-hidden shadow-lg shadow-black/40">
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-2">
        <span className="text-emerald-400 font-bold flex items-center gap-1.5">
          <Zap className={`w-3.5 h-3.5 ${isProcessing ? "text-amber-400 animate-pulse" : isSpeaking ? "text-emerald-400" : "text-slate-500"}`} />
          MULTI-AGENT REASONING PIPELINE
        </span>
        <span className="text-slate-400 font-semibold">
          {activeStep === 0 ? "Standby" : activeStep === 5 ? "Phase 5/5 Active • Speaking" : `Phase ${activeStep}/5 Active`}
        </span>
      </div>

      <div className="relative flex items-start justify-between gap-1 py-1">
        {/* Connecting track line */}
        <div className="absolute top-4 left-4 right-4 h-[2px] bg-slate-800/90 -z-10" />

        {PIPELINE_STEPS.map((s) => {
          const Icon = s.icon;
          const isActive = activeStep === s.step;
          const isDone = activeStep > s.step;

          return (
            <div key={s.step} className="flex-1 flex flex-col items-center text-center">
              <motion.div
                className={`relative flex h-9 w-9 items-center justify-center rounded-full border text-xs transition-all duration-300 ${
                  isDone
                    ? "border-emerald-500 bg-emerald-950/80 text-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.3)]"
                    : isActive
                    ? "border-emerald-400 bg-emerald-500/20 text-emerald-300 shadow-[0_0_18px_rgba(52,211,153,0.6)]"
                    : "border-slate-800 bg-slate-950 text-slate-600"
                }`}
                animate={isActive ? { scale: [1, 1.14, 1] } : { scale: 1 }}
                transition={
                  isActive
                    ? { repeat: Infinity, duration: 1.1, ease: "easeInOut" }
                    : { duration: 0.2 }
                }
              >
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
                {isActive && (
                  <span className="absolute -inset-1.5 animate-ping rounded-full border border-emerald-400/50 opacity-75" />
                )}
              </motion.div>

              <span
                className={`mt-1.5 text-[10px] font-medium leading-tight transition-colors ${
                  isActive
                    ? "text-emerald-300 font-bold"
                    : isDone
                    ? "text-emerald-400 font-semibold"
                    : "text-slate-500"
                }`}
              >
                {s.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Memoize — re-renders when activeStep changes
export const AIReasoningPipeline = memo(AIReasoningPipelineInner);
