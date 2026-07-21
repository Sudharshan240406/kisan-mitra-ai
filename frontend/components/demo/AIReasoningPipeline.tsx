"use client";

import React, { memo, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Server, BookOpen, Cpu, Volume2, CheckCircle2, Zap, Loader2 } from "lucide-react";

interface AIReasoningPipelineProps {
  activeStep: number; // 0: Idle, 1: STT, 2: Digital Twin, 3: RAG, 4: Reasoning, 5: Voice
}

const PIPELINE_STEPS = [
  {
    step: 1,
    label: "Speech STT",
    icon: Mic,
    desc: "Audio ingestion & transcription",
    color: "cyan",
  },
  {
    step: 2,
    label: "Digital Twin",
    icon: Server,
    desc: "Farmer profile & land records",
    color: "blue",
  },
  {
    step: 3,
    label: "Scheme RAG",
    icon: BookOpen,
    desc: "Eligibility rules engine",
    color: "violet",
  },
  {
    step: 4,
    label: "AI Reasoning",
    icon: Cpu,
    desc: "LangGraph multi-agent graph",
    color: "amber",
  },
  {
    step: 5,
    label: "Voice Output",
    icon: Volume2,
    desc: "Multilingual TTS synthesis",
    color: "emerald",
  },
];

// Progress bar that fills from 0→100% over `durationMs`
function StageProgressBar({ durationMs, color }: { durationMs: number; color: string }) {
  const colorMap: Record<string, string> = {
    cyan:    "from-cyan-500 to-cyan-400",
    blue:    "from-blue-500 to-blue-400",
    violet:  "from-violet-500 to-violet-400",
    amber:   "from-amber-500 to-amber-400",
    emerald: "from-emerald-500 to-emerald-400",
  };
  const gradient = colorMap[color] ?? colorMap.emerald;

  return (
    <motion.div
      className={`h-[3px] rounded-full bg-gradient-to-r ${gradient}`}
      initial={{ width: "0%" }}
      animate={{ width: "100%" }}
      transition={{ duration: durationMs / 1000, ease: "linear" }}
    />
  );
}

// Duration for progress bar per stage (ms) — slightly shorter than actual hold so it fills before transition
const STAGE_PROGRESS_DURATION: Record<number, number> = {
  1: 820,
  2: 820,
  3: 1100,
  4: 1600,
  5: 6000,  // long; Voice Output stays until audio ends
};

function AIReasoningPipelineInner({ activeStep }: AIReasoningPipelineProps) {
  const isProcessing = activeStep > 0 && activeStep < 5;
  const isSpeaking   = activeStep === 5;
  const isActive     = activeStep > 0;

  // Track which step became active most recently to restart progress bar
  const [progressKey, setProgressKey] = useState(0);
  const prevStep = useRef(0);
  useEffect(() => {
    if (activeStep !== prevStep.current) {
      prevStep.current = activeStep;
      setProgressKey((k) => k + 1);
    }
  }, [activeStep]);

  // Header status label
  const statusLabel =
    activeStep === 0 ? "Standby"
    : activeStep === 5 ? "Phase 5/5 • Speaking"
    : `Phase ${activeStep}/5 Active`;

  // Header Zap color
  const zapColor =
    isProcessing ? "text-amber-400 animate-pulse"
    : isSpeaking  ? "text-emerald-400 animate-pulse"
    : "text-slate-500";

  return (
    <div className="my-3 rounded-2xl border border-slate-700/60 bg-slate-900/90 backdrop-blur-md overflow-hidden shadow-xl shadow-black/50">

      {/* ── HEADER ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 pt-3 pb-2">
        <span className="text-emerald-400 font-bold font-mono text-[11px] flex items-center gap-1.5 tracking-wide">
          <Zap className={`w-3.5 h-3.5 ${zapColor}`} />
          MULTI-AGENT REASONING PIPELINE
        </span>
        <motion.span
          key={statusLabel}
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className={`text-[11px] font-mono font-semibold ${
            isSpeaking ? "text-emerald-400" : isProcessing ? "text-amber-400" : "text-slate-500"
          }`}
        >
          {statusLabel}
        </motion.span>
      </div>

      {/* ── STAGE NODES + TRACK ────────────────────────────────── */}
      <div className="relative px-3 pb-1">
        {/* Background track */}
        <div className="absolute top-[18px] left-8 right-8 h-[2px] bg-slate-800/90 rounded-full" />

        {/* Completed track glow — fills from left to current step */}
        {activeStep > 1 && (
          <motion.div
            className="absolute top-[18px] left-8 h-[2px] rounded-full bg-gradient-to-r from-emerald-600 to-emerald-400"
            initial={{ width: "0%" }}
            animate={{
              width: `${Math.min(((activeStep - 1) / 4) * 100, 100)}%`,
            }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        )}

        {/* Step nodes */}
        <div className="relative flex items-start justify-between gap-1 py-1">
          {PIPELINE_STEPS.map((s) => {
            const Icon = s.icon;
            const isStepActive = activeStep === s.step;
            const isStepDone   = activeStep > s.step;

            const colorGlow: Record<string, string> = {
              cyan:    "shadow-[0_0_20px_rgba(34,211,238,0.55)]  border-cyan-400    bg-cyan-500/15    text-cyan-300",
              blue:    "shadow-[0_0_20px_rgba(96,165,250,0.55)]  border-blue-400    bg-blue-500/15    text-blue-300",
              violet:  "shadow-[0_0_20px_rgba(167,139,250,0.55)] border-violet-400  bg-violet-500/15  text-violet-300",
              amber:   "shadow-[0_0_20px_rgba(251,191,36,0.55)]  border-amber-400   bg-amber-500/15   text-amber-300",
              emerald: "shadow-[0_0_20px_rgba(52,211,153,0.55)]  border-emerald-400 bg-emerald-500/15 text-emerald-300",
            };

            const nodeClass = isStepDone
              ? "border-emerald-500 bg-emerald-950/70 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]"
              : isStepActive
              ? colorGlow[s.color]
              : "border-slate-700 bg-slate-950 text-slate-600";

            return (
              <div key={s.step} className="flex-1 flex flex-col items-center text-center">
                {/* Node circle */}
                <motion.div
                  className={`relative flex h-9 w-9 items-center justify-center rounded-full border transition-all duration-300 ${nodeClass}`}
                  animate={isStepActive ? { scale: [1, 1.12, 1] } : { scale: 1 }}
                  transition={
                    isStepActive
                      ? { repeat: Infinity, duration: 1.2, ease: "easeInOut" }
                      : { duration: 0.25 }
                  }
                >
                  {/* Done checkmark */}
                  {isStepDone ? (
                    <motion.div
                      initial={{ scale: 0, rotate: -30 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: "spring", stiffness: 400, damping: 20 }}
                    >
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    </motion.div>
                  ) : isStepActive ? (
                    <>
                      <Icon className="w-4 h-4" />
                      {/* Ping ring */}
                      <span className="absolute -inset-1.5 animate-ping rounded-full border border-current opacity-60" />
                      {/* Slow outer glow ring */}
                      <motion.span
                        className="absolute -inset-2.5 rounded-full border border-current opacity-20"
                        animate={{ scale: [1, 1.3, 1], opacity: [0.2, 0, 0.2] }}
                        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
                      />
                    </>
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </motion.div>

                {/* Label */}
                <AnimatePresence mode="wait">
                  <motion.span
                    key={`label-${s.step}-${isStepActive ? "active" : isStepDone ? "done" : "idle"}`}
                    initial={{ opacity: 0, y: 2 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -2 }}
                    transition={{ duration: 0.2 }}
                    className={`mt-1.5 text-[10px] font-medium leading-tight transition-colors ${
                      isStepActive
                        ? "text-white font-bold"
                        : isStepDone
                        ? "text-emerald-400 font-semibold"
                        : "text-slate-600"
                    }`}
                  >
                    {s.label}
                  </motion.span>
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── ACTIVE STAGE DETAIL BAR ────────────────────────────── */}
      <AnimatePresence mode="wait">
        {activeStep > 0 && (
          <motion.div
            key={`detail-${activeStep}`}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden"
          >
            {/* Stage description row */}
            <div className="mx-3 mb-1 flex items-center justify-between gap-2 rounded-lg bg-slate-800/50 border border-slate-700/40 px-3 py-1.5">
              <div className="flex items-center gap-2 min-w-0">
                <Loader2 className="w-3 h-3 text-emerald-400 animate-spin shrink-0" />
                <span className="text-[10px] font-mono text-slate-300 font-medium truncate">
                  {PIPELINE_STEPS.find((s) => s.step === activeStep)?.desc ?? "Processing…"}
                </span>
              </div>
              <span className="text-[10px] font-mono text-slate-500 shrink-0">
                {activeStep}/5
              </span>
            </div>

            {/* Progress bar */}
            <div className="mx-3 mb-3 h-[3px] rounded-full bg-slate-800/80 overflow-hidden">
              <StageProgressBar
                key={`pb-${progressKey}`}
                durationMs={STAGE_PROGRESS_DURATION[activeStep] ?? 1000}
                color={PIPELINE_STEPS.find((s) => s.step === activeStep)?.color ?? "emerald"}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Only re-render when activeStep changes
export const AIReasoningPipeline = memo(AIReasoningPipelineInner);
