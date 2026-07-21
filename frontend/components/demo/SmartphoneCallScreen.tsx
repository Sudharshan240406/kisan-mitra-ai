"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Users, Globe2, ChevronDown, Check, AlertTriangle } from "lucide-react";
import { useDemoCallSession, SUPPORTED_LANGUAGES, LanguageOption } from "@/hooks/useDemoCallSession";
import { FarmerAvatarCard } from "./FarmerAvatarCard";
import { AudioWaveformVisualizer } from "./AudioWaveformVisualizer";
import { AIReasoningPipeline } from "./AIReasoningPipeline";
import { LiveTranscriptStream } from "./LiveTranscriptStream";
import { CallActionButtons } from "./CallActionButtons";

interface SmartphoneCallScreenProps {
  onClose: () => void;
}

/* ════════════════════════════════════════════════════════════
   PREMIUM LANGUAGE SELECTOR DROPDOWN
   ════════════════════════════════════════════════════════════ */

interface LanguageSelectorProps {
  value: string;
  onChange: (code: string) => void;
}

function LanguageSelector({ value, onChange }: LanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = SUPPORTED_LANGUAGES.find((l) => l.code === value) || SUPPORTED_LANGUAGES[0];

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={ref} className="relative select-none">
      {/* Trigger button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 border border-emerald-500/40 hover:border-emerald-400/70 text-emerald-300 text-[12px] font-semibold font-mono transition-all"
        title="Select Conversation Language"
      >
        <span className="text-base leading-none">{selected.flag}</span>
        <span>{selected.label}</span>
        <span className="text-slate-500 text-[10px] ml-0.5">{selected.nativeName}</span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {/* Dropdown panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute right-0 top-full mt-1.5 z-50 w-56 rounded-2xl border border-emerald-500/30 bg-slate-950/95 backdrop-blur-xl shadow-2xl shadow-black/60 overflow-hidden"
          >
            <div className="px-3 pt-2.5 pb-1.5 border-b border-slate-800/70">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 font-mono">
                Conversation Language
              </p>
            </div>
            <div className="py-1 max-h-72 overflow-y-auto">
              {SUPPORTED_LANGUAGES.map((lang) => {
                const isActive = lang.code === value;
                return (
                  <button
                    key={lang.code}
                    onClick={() => {
                      onChange(lang.code);
                      setOpen(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-all hover:bg-emerald-500/10 ${
                      isActive ? "bg-emerald-500/15" : ""
                    }`}
                  >
                    <span className="text-lg leading-none w-6 text-center">{lang.flag}</span>
                    <div className="flex flex-col min-w-0 flex-1">
                      <span className={`text-[13px] font-semibold leading-tight ${isActive ? "text-emerald-300" : "text-slate-200"}`}>
                        {lang.label}
                      </span>
                      <span className="text-[11px] text-slate-500 leading-tight">{lang.nativeName}</span>
                    </div>
                    {isActive && (
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ════════════════════════════════════════════════════════════
   MAIN SMARTPHONE CALL SCREEN
   ════════════════════════════════════════════════════════════ */

export function SmartphoneCallScreen({ onClose }: SmartphoneCallScreenProps) {
  const {
    farmers,
    selectedFarmer,
    setSelectedFarmer,
    selectedLanguage,
    setSelectedLanguage,
    callState,
    callDuration,
    transcript,
    activePipelineStep,
    isMuted,
    setIsMuted,
    isListening,
    isTtsPlaying,
    aiResponseData,
    ttsWarning,
    acceptCall,
    rejectCall,
    endCall,
    toggleMicListening,
    submitPresetQuery,
    triggerIncomingCall,
  } = useDemoCallSession();

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const activeLang = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];

  return (
    <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-emerald-500/30 bg-slate-950/98 shadow-2xl backdrop-blur-2xl text-white flex flex-col">

      {/* ── TOP HEADER ────────────────────────────────────────── */}
      <div className="flex items-center justify-between border-b border-slate-800/80 px-5 py-3 shrink-0">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
          </span>
          <span className="font-mono text-xs font-bold tracking-wider text-emerald-400">
            {callState === "incoming"
              ? "INCOMING FARMER CALL..."
              : callState === "ended"
              ? "CALL TERMINATED"
              : `CALL CONNECTED • ${formatTimer(callDuration)}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Close button */}
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-800 hover:text-white transition-all"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* ── LANGUAGE SELECTOR BANNER ──────────────────────────── */}
      <div className="flex items-center justify-between gap-3 border-b border-slate-800/60 bg-slate-900/40 px-5 py-2.5 shrink-0">
        <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400">
          <Globe2 className="w-3.5 h-3.5 text-emerald-400" />
          <span className="uppercase tracking-wider font-bold text-slate-500">Conversation Language:</span>
          <span className="text-emerald-300 font-bold">
            {activeLang.flag} {activeLang.label} ({activeLang.nativeName})
          </span>
        </div>
        <LanguageSelector value={selectedLanguage} onChange={setSelectedLanguage} />
      </div>

      {/* ── SCROLLABLE CONTENT AREA ───────────────────────────── */}
      <div className="flex-1 overflow-y-auto overscroll-contain px-5 py-3" style={{ maxHeight: "calc(100dvh - 180px)" }}>

        {/* Cloud TTS Warning Banner */}
        {ttsWarning && (
          <div className="mb-3 flex items-center gap-2 rounded-xl bg-amber-500/10 border border-amber-500/30 px-3 py-2 text-[11px] text-amber-300 font-mono">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{ttsWarning}</span>
          </div>
        )}

        {/* Farmer Profile Tabs */}
        <div className="mb-3 flex items-center justify-between gap-2 overflow-x-auto pb-1 text-xs shrink-0">
          <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1 shrink-0">
            <Users className="w-3 h-3 text-emerald-400" />
            Farmer Profile:
          </span>
          <div className="flex gap-1.5 overflow-x-auto">
            {farmers.map((f) => (
              <button
                key={f.farmer_id}
                onClick={() => triggerIncomingCall(f)}
                className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all shrink-0 ${
                  selectedFarmer.farmer_id === f.farmer_id
                    ? "bg-emerald-900/80 border-emerald-400 text-emerald-200"
                    : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                {f.name} ({f.state})
              </button>
            ))}
          </div>
        </div>

        {/* Farmer Avatar */}
        <FarmerAvatarCard farmer={selectedFarmer} callState={callState} />

        {/* Audio Waveform */}
        <AudioWaveformVisualizer
          isActive={callState !== "idle" && callState !== "ended"}
          isSpeaking={isTtsPlaying}
          isListening={isListening}
        />

        {/* AI Reasoning Pipeline */}
        <AIReasoningPipeline activeStep={activePipelineStep} />

        {/* Live Transcript */}
        <LiveTranscriptStream
          transcript={transcript}
          aiResponseData={aiResponseData}
          selectedLanguage={selectedLanguage}
        />

        {/* Action Buttons */}
        <CallActionButtons
          callState={callState}
          onAccept={acceptCall}
          onReject={rejectCall}
          onEnd={endCall}
          onToggleMic={toggleMicListening}
          onPresetQuery={submitPresetQuery}
          isListening={isListening}
          isMuted={isMuted}
          onToggleMute={() => setIsMuted(!isMuted)}
          language={selectedLanguage}
        />
      </div>
    </div>
  );
}
