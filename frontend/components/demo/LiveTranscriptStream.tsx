"use client";

import React, { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Bot, Sparkles, Volume2, Globe2 } from "lucide-react";
import { TranscriptTurn, SUPPORTED_LANGUAGES } from "@/hooks/useDemoCallSession";

interface LiveTranscriptStreamProps {
  transcript: TranscriptTurn[];
  aiResponseData?: any;
  selectedLanguage: string;
}

export function LiveTranscriptStream({
  transcript,
  aiResponseData,
  selectedLanguage,
}: LiveTranscriptStreamProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to bottom on new messages — stable, uses endRef so no jumpiness
  useEffect(() => {
    if (endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [transcript.length]);

  const activeLang =
    SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) ||
    SUPPORTED_LANGUAGES[0];

  return (
    <div className="my-3 rounded-2xl border border-slate-800/80 bg-slate-950/80 backdrop-blur-md overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-3.5 py-2 border-b border-slate-800/60">
        <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          LIVE TRANSCRIPT
        </span>
        <span className="flex items-center gap-1.5 text-slate-500">
          <Globe2 className="w-3 h-3 text-emerald-400" />
          <span className="text-emerald-300 font-semibold">
            {activeLang.flag} {activeLang.label}
          </span>
          <span className="text-slate-600">•</span>
          <span>{transcript.length} turns</span>
        </span>
      </div>

      {/* Transcript body — fixed height, internal scroll */}
      <div
        ref={containerRef}
        className="h-52 overflow-y-auto overscroll-contain p-3 space-y-2.5 font-sans text-xs"
        style={{ scrollbarWidth: "thin" }}
      >
        <AnimatePresence initial={false}>
          {transcript.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-4 text-center text-slate-500">
              <Bot className="w-8 h-8 mb-2 stroke-1 opacity-50 text-slate-400 animate-pulse" />
              <p>Waiting for voice prompt or microphone speech...</p>
              <p className="text-[10px] text-slate-600 mt-0.5">
                Click &ldquo;Speak into Mic&rdquo; or select a sample question below.
              </p>
            </div>
          ) : (
            transcript.map((turn) => (
              <motion.div
                key={turn.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex gap-2.5 rounded-xl p-2.5 border ${
                  turn.role === "farmer"
                    ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-100 ml-4"
                    : turn.role === "assistant"
                    ? "bg-slate-900/90 border-cyan-500/30 text-slate-200 mr-4 shadow-sm shadow-cyan-950/40"
                    : "bg-slate-950 border-slate-800 text-slate-400 text-[11px] justify-center text-center font-mono"
                }`}
              >
                {turn.role !== "system" && (
                  <div
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs ${
                      turn.role === "farmer"
                        ? "border-emerald-400/50 bg-emerald-900/80 text-emerald-300"
                        : "border-cyan-400/50 bg-cyan-900/80 text-cyan-300"
                    }`}
                  >
                    {turn.role === "farmer" ? (
                      <User className="w-3.5 h-3.5" />
                    ) : (
                      <Bot className="w-3.5 h-3.5" />
                    )}
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  {/* Role label + timestamp */}
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5 font-mono">
                    <span className="font-semibold text-slate-300">
                      {turn.role === "farmer"
                        ? "Farmer"
                        : turn.role === "assistant"
                        ? "Kisan Mitra AI"
                        : "System"}
                    </span>
                    <span>{turn.timestamp}</span>
                  </div>

                  {/* Transcript text — in the selected language */}
                  <p className="leading-relaxed font-sans text-[13px] break-words">{turn.text}</p>

                  {/* Language badge — clean, no debug text */}
                  {turn.role === "assistant" && turn.languageCode && (
                    <div className="mt-1.5 flex items-center gap-1 text-[10px] font-mono">
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
                        <Volume2 className="w-3 h-3" />
                        {activeLang.flag} {activeLang.label} Voice
                      </span>
                    </div>
                  )}

                  {/* Scheme chip */}
                  {turn.role === "assistant" && aiResponseData?.top_scheme && (
                    <div className="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/30 text-emerald-300 text-[10px] font-semibold">
                      ✓ {aiResponseData.top_scheme}
                    </div>
                  )}
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
        {/* Invisible element at end to scroll into view */}
        <div ref={endRef} />
      </div>
    </div>
  );
}
