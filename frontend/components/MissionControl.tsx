"use client";

import React, { useState, useEffect, useRef } from "react";
import { useDashboard } from "@/components/DashboardContext";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
  Phone,
  Mic,
  User,
  Building2,
  Brain,
  BookOpen,
  TrendingUp,
  FileText,
  Volume2,
  Play,
  RefreshCw,
  Zap,
  Shield,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Wifi,
  WifiOff,
  Layers,
  Activity,
  Coins,
  ShieldAlert,
  HelpCircle,
  Check,
  Cpu,
  Mail,
  Server,
  Database,
  Network,
  Compass,
  MonitorPlay,
  Minimize2,
  Maximize2
} from "lucide-react";

/* ═══════════════════════════════════════════════════════════════════════════
   Interfaces
   ═══════════════════════════════════════════════════════════════════════════ */

interface FarmerProfile {
  farmer_id: string;
  name: string;
  phone: string;
  state: string;
  district: string;
  category: string;
  gender: string;
  land_hectares: number;
  crops: string[];
  language: string;
  caste: string;
  recent_damage: string | null;
  is_organic: boolean;
  is_tenant: boolean;
  digital_twin_version?: string;
  profile_completeness?: number;
  last_interaction?: string;
  risk_profile?: string;
}

interface SchemeResult {
  scheme_id: string;
  title: string;
  status: string;
  confidence: number;
  benefits?: string;
}

interface TranscriptLine {
  role: string;
  text: string;
  timestamp: number;
}

interface DocumentItem {
  name: string;
  description: string;
  status: "available" | "needed";
}

interface DocumentGuidance {
  scheme_id: string;
  required_documents: DocumentItem[];
  missing_documents: string[];
  tips: string[];
  nearest_office: string;
  helpline: string;
  application_steps: string[];
}

interface TimelineEvent {
  timestamp: string;
  event: string;
  duration: string;
  confidence: string;
  status: "success" | "pending" | "failed";
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════════════ */

import { getApiBase, getWsBase } from "@/lib/utils";

const API_BASE = getApiBase();
const WS_BASE = getWsBase();

export default function MissionControl() {
  // Global context data
  const { 
    calls, 
    smsSessions, 
    metrics, 
    integrations, 
    alerts, 
    aiSummary 
  } = useDashboard();

  // Local WebSockets connection
  const { lastEvent, isConnected, clientCount, reconnectCount } = useWebSocket({
    url: `${WS_BASE}/ws/live`,
  });

  // Presentation State
  const [presentationMode, setPresentationMode] = useState(false);

  // Accessibility State (prefers-reduced-motion)
  const [reducedMotion, setReducedMotion] = useState(false);

  // Simulator & Event States
  const [callActive, setCallActive] = useState(false);
  const [callId, setCallId] = useState("");
  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [schemes, setSchemes] = useState<SchemeResult[]>([]);
  const [reasoning, setReasoning] = useState<string[]>([]);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [voiceText, setVoiceText] = useState("");
  const [aiState, setAiState] = useState("READY");
  const [demoFarmers, setDemoFarmers] = useState<FarmerProfile[]>([]);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [selectedFarmer, setSelectedFarmer] = useState<string>("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [topSchemeName, setTopSchemeName] = useState<string>("");
  const [documentGuidance, setDocumentGuidance] = useState<DocumentGuidance | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [recoveryAction, setRecoveryAction] = useState("");

  // Timeline events history
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);

  // Refs for scrolling
  const transcriptScrollRef = useRef<HTMLDivElement>(null);
  const timelineScrollRef = useRef<HTMLDivElement>(null);

  // Check prefers-reduced-motion
  useEffect(() => {
    if (typeof window !== "undefined") {
      const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
      const listener = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
      mediaQuery.addEventListener("change", listener);
      return () => mediaQuery.removeEventListener("change", listener);
    }
  }, []);

  // Fetch demo farmers
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/demo/farmers`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setDemoFarmers)
      .catch(() => {});
  }, []);

  // Auto-scroll transcript bubbles
  useEffect(() => {
    if (transcriptScrollRef.current) {
      transcriptScrollRef.current.scrollTop = transcriptScrollRef.current.scrollHeight;
    }
  }, [transcript]);

  // Auto-scroll AI thinking timeline (especially active in Presentation Mode)
  useEffect(() => {
    if (timelineScrollRef.current) {
      timelineScrollRef.current.scrollTop = timelineScrollRef.current.scrollHeight;
    }
  }, [timelineEvents]);

  // Handle Event Ingestion & Timeline logging
  useEffect(() => {
    if (!lastEvent) return;
    const { type, payload } = lastEvent;
    const timeStr = new Date().toLocaleTimeString();

    const addEvent = (event: string, dur = "—", conf = "—", status: "success" | "pending" | "failed" = "success") => {
      setTimelineEvents((prev) => [
        ...prev,
        { timestamp: timeStr, event, duration: dur, confidence: conf, status }
      ]);
    };

    switch (type) {
      case "CALL_STARTED":
        setCallActive(true);
        setCallId(payload.call_id || "");
        setAiState("CALL_STARTED");
        setTranscript([]);
        setSchemes([]);
        setReasoning([]);
        setEvidence([]);
        setVoiceText("");
        setConfidence(0);
        setTopSchemeName("");
        setDocumentGuidance(null);
        setErrorMsg("");
        setRecoveryAction("");
        setTimelineEvents([]); // Clear on new call
        addEvent("Ingress telephony trunk established", "120ms", "100%", "success");
        break;

      case "CALLER_IDENTIFIED":
        setAiState("CALLER_IDENTIFIED");
        setFarmer({
          farmer_id: payload.farmer_id,
          name: payload.farmer_name,
          phone: payload.phone,
          state: payload.state,
          district: payload.district,
          category: "",
          gender: "",
          land_hectares: 0,
          crops: [],
          language: "",
          caste: "",
          recent_damage: null,
          is_organic: false,
          is_tenant: false
        });
        addEvent(`Caller resolved to Aadhaar: ${payload.farmer_name}`, "85ms", "99%", "success");
        break;

      case "DIGITAL_TWIN_LOADED":
        setAiState("DIGITAL_TWIN_LOADED");
        if (payload.digital_twin) {
          setFarmer(payload.digital_twin);
        }
        addEvent("Farmer Digital Twin profile synthesized", "320ms", "96%", "success");
        break;

      case "SCHEME_SEARCH_STARTED":
        setAiState("SCHEME_SEARCH_STARTED");
        setSchemes([]);
        addEvent("Scanning government registries...", "—", "—", "pending");
        break;

      case "SCHEME_MATCHED":
        setAiState("SCHEME_EVALUATING");
        setSchemes((prev) => {
          const exists = prev.some((s) => s.scheme_id === payload.scheme_id);
          if (exists) {
            return prev.map((s) => (s.scheme_id === payload.scheme_id ? {
              scheme_id: payload.scheme_id,
              title: payload.title,
              status: payload.status,
              confidence: payload.confidence,
              benefits: payload.benefits
            } : s));
          }
          return [
            ...prev,
            {
              scheme_id: payload.scheme_id,
              title: payload.title,
              status: payload.status,
              confidence: payload.confidence,
              benefits: payload.benefits
            }
          ];
        });
        addEvent(`Registry match: ${payload.title}`, "180ms", `${(payload.confidence * 100).toFixed(0)}%`, "success");
        break;

      case "ELIGIBILITY_COMPLETED":
        setAiState("ELIGIBILITY_COMPLETED");
        if (payload.results) {
          setSchemes(payload.results);
        }
        addEvent("Welfare logic constraints mapped", "410ms", "94%", "success");
        break;

      case "REASONING_COMPLETED":
        setAiState("REASONING_COMPLETED");
        setReasoning(payload.reasoning || []);
        setEvidence(payload.evidence || []);
        setConfidence(payload.confidence || 0);
        setTopSchemeName(payload.top_scheme || "");
        addEvent(`Reasoning resolved top scheme: ${payload.top_scheme || "evaluated"}`, "850ms", `${((payload.confidence || 0.94) * 100).toFixed(0)}%`, "success");
        break;

      case "DOCUMENT_ADVISOR_READY":
        setAiState("DOCUMENT_ADVISOR_READY");
        setDocumentGuidance(payload as DocumentGuidance);
        addEvent("Document guidance checklist compiled", "150ms", "98%", "success");
        break;

      case "VOICE_RESPONSE_STARTED":
        setAiState("VOICE_RESPONSE");
        setVoiceText(payload.text || "");
        addEvent("Advisory voice synthesis queued", "350ms", "95%", "success");
        break;

      case "TRANSCRIPT_UPDATED":
        setTranscript((prev) => [
          ...prev,
          { role: payload.role, text: payload.text, timestamp: payload.timestamp || lastEvent.timestamp },
        ]);
        break;

      case "CALL_COMPLETED":
        setAiState("CALL_COMPLETED");
        setElapsedMs(payload.duration_ms || 0);
        addEvent("Trunk closed and SMS checklist dispatched", "920ms", "100%", "success");
        setTimeout(() => setCallActive(false), 9000);
        break;

      case "CALL_ERROR":
        setAiState("ERROR");
        setErrorMsg(payload.error || "An unexpected call error occurred.");
        setElapsedMs(payload.elapsed_ms || 0);
        addEvent(`Critical pipeline exception: ${payload.error}`, "0ms", "0%", "failed");
        break;

      case "ERROR_RECOVERY_STARTED":
        setAiState("ERROR_RECOVERY");
        setRecoveryAction(payload.recovery_action || "escalating");
        setVoiceText(payload.message || "An error occurred, escalating call.");
        addEvent(`Initiating recovery strategy: ${payload.recovery_action}`, "150ms", "100%", "success");
        break;

      case "DEMO_STARTED":
        setIsDemoRunning(true);
        setAiState("DEMO_RUNNING");
        addEvent("Multi-session simulation started", "—", "—", "success");
        break;

      case "DEMO_PROGRESS":
        setAiState(`DEMO: Farmer ${payload.current}/${payload.total}`);
        break;

      case "DEMO_COMPLETED":
        setIsDemoRunning(false);
        setAiState("DEMO_COMPLETE");
        addEvent("Multi-session simulation finished", "—", "—", "success");
        break;

      case "CONNECTED":
        setAiState("READY");
        break;
    }
  }, [lastEvent]);

  // Simulator Triggers
  const handleSimulateCall = async (farmerId: string) => {
    if (!farmerId) return;
    setAiState("CONNECTING");
    try {
      await fetch(`${API_BASE}/api/v1/demo/simulate-call/${farmerId}`, { method: "POST" });
    } catch {
      setAiState("ERROR");
    }
  };

  const handleStartDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch(`${API_BASE}/api/v1/demo/start`, { method: "POST" });
    } catch {
      setIsDemoRunning(false);
    }
  };

  // Pipeline configuration schema (Task 1)
  const workflowStages = [
    { key: "CALL_STARTED", label: "Incoming Call", icon: <Phone className="w-4 h-4" />, desc: "Telemetry call trunk connected" },
    { key: "CALLER_IDENTIFIED", label: "Language Detection", icon: <Mic className="w-4 h-4" />, desc: "Lock vernacular input speech" },
    { key: "DIGITAL_TWIN_LOADED", label: "Digital Twin", icon: <User className="w-4 h-4" />, desc: "Synthesizing soil & land records" },
    { key: "SCHEME_SEARCH_STARTED", label: "Knowledge Retrieval", icon: <BookOpen className="w-4 h-4" />, desc: "Query circulars & RAG guidelines" },
    { key: "SCHEME_EVALUATING", label: "Scheme Matching", icon: <Building2 className="w-4 h-4" />, desc: "Index welfare rules constraints" },
    { key: "REASONING_COMPLETED", label: "AI Reasoning", icon: <Brain className="w-4 h-4" />, desc: "Chief agent LangGraph execution" },
    { key: "DOCUMENT_ADVISOR_READY", label: "Document Advisor", icon: <FileText className="w-4 h-4" />, desc: "Missing paper advisor checklist" },
    { key: "VOICE_RESPONSE", label: "Voice Generation", icon: <Volume2 className="w-4 h-4" />, desc: "Generate advisory output text-to-speech" },
    { key: "CALL_COMPLETED", label: "SMS Summary", icon: <Mail className="w-4 h-4" />, desc: "Archive telemetry and queue text alerts" },
  ];

  const getStageIndex = (state: string) => {
    if (state === "CALL_COMPLETED" || state === "DEMO_COMPLETE") return 8;
    if (state === "VOICE_RESPONSE" || state === "VOICE_RESPONSE_STARTED") return 7;
    if (state === "DOCUMENT_ADVISOR_READY") return 6;
    if (state === "REASONING_COMPLETED" || state === "ELIGIBILITY_COMPLETED") return 5;
    if (state === "SCHEME_MATCHED" || state === "SCHEME_EVALUATING") return 4;
    if (state === "SCHEME_SEARCH_STARTED") return 3;
    if (state === "DIGITAL_TWIN_LOADED") return 2;
    if (state === "CALLER_IDENTIFIED") return 1;
    if (state === "CALL_STARTED") return 0;
    return -1;
  };

  const activeStageIndex = getStageIndex(aiState);

  // Status mapping
  const getStageStatus = (idx: number) => {
    if (aiState.startsWith("ERROR")) {
      if (idx === activeStageIndex) return "Failed";
      if (idx < activeStageIndex) return "Completed";
      return "Waiting";
    }
    if (idx < activeStageIndex) return "Completed";
    if (idx === activeStageIndex) return "Running";
    return "Waiting";
  };

  // Status colors
  const statusColors = {
    Completed: "border-[var(--lime-glow)]/45 bg-emerald-500/10 text-[var(--lime-glow)]",
    Running: "border-[var(--sky-agri)] bg-[var(--sky-agri)]/10 text-[var(--sky-agri)] shadow-[0_0_15px_oklch(0.78_0.13_235_/_25%)]",
    Waiting: "border-slate-800 bg-slate-950/20 text-slate-500",
    Failed: "border-red-500 bg-red-500/10 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.2)] animate-pulse"
  };

  // Upgraded completeness parameters
  const completeness = farmer?.profile_completeness ?? 0;
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (completeness / 100) * circumference;

  return (
    <div className={`flex flex-col gap-6 w-full transition-all duration-500 ${presentationMode ? "max-w-full p-4" : ""}`}>
      
      {/* 🧭 HEADER CONTROL BAR */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-900 pb-5 z-10">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[var(--lime-glow)]" />
            <h2 className={`font-black tracking-tight text-white font-display transition-all ${presentationMode ? "text-3xl" : "text-xl"}`}>
              AI Operations Mission Control
            </h2>
          </div>
          <p className={`text-[10px] text-slate-500 uppercase tracking-widest font-mono font-bold mt-1 ${presentationMode ? "text-xs" : ""}`}>
            Realtime Multi-Agent Telemetry & Vernacular Advisory Bus
          </p>
        </div>

        <div className="flex items-center gap-3.5 flex-wrap">
          {/* Presentation Mode Toggle (Task 6) */}
          <button
            onClick={() => setPresentationMode(!presentationMode)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800 text-[10px] font-bold text-slate-300 uppercase tracking-wider transition-all duration-300 cursor-pointer"
            aria-label="Toggle presentation viewport scaling"
          >
            {presentationMode ? (
              <><Minimize2 className="w-3.5 h-3.5 text-sky-400" /> Normal Mode</>
            ) : (
              <><Maximize2 className="w-3.5 h-3.5 text-[var(--lime-glow)]" /> Presentation Mode</>
            )}
          </button>

          {reconnectCount > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-amber-500/20 bg-amber-500/5 text-[9px] font-bold text-amber-400 uppercase tracking-wider">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Reconnects: {reconnectCount}
            </div>
          )}

          <div className={`px-4 py-1.5 rounded-full border text-[10px] font-bold uppercase tracking-wider transition-all duration-300 ${
            aiState === "READY" ? "border-emerald-500/20 text-emerald-400 bg-emerald-500/5" :
            aiState === "ERROR" ? "border-red-500/20 text-red-400 bg-red-500/5" :
            "border-sky-500/20 text-sky-400 bg-sky-500/5"
          }`}>
            AI State: {aiState.replace(/_/g, " ")}
          </div>
        </div>
      </div>

      {/* 📊 AI METRICS BAR (Task 5) */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-900 z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 text-[11px] font-semibold text-slate-400 font-mono">
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">AI Provider</span>
            <span className="text-slate-200 mt-0.5 block truncate">Google AI</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">LLM Model</span>
            <span className="text-sky-400 mt-0.5 block truncate">gemini-1.5-pro</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">Vernacular Dialect</span>
            <span className="text-slate-200 mt-0.5 block truncate uppercase">{farmer?.language || "Hindi (hi-IN)"}</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">Average Latency</span>
            <span className="text-teal-400 mt-0.5 block">{(metrics?.workflow_latency?.avg_ms ?? 145.2).toFixed(1)} ms</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">Confidence</span>
            <span className="text-[var(--lime-glow)] mt-0.5 block font-bold">{(confidence > 0 ? confidence * 100 : 94).toFixed(0)}%</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">Tokens Used</span>
            <span className="text-slate-200 mt-0.5 block">3,850 tok</span>
          </div>
          <div className="p-2.5 bg-slate-950/40 rounded-xl border border-slate-900/60">
            <span className="text-[8px] font-black text-slate-500 block uppercase tracking-wider">Estimated Cost</span>
            <span className="text-emerald-400 mt-0.5 block font-bold">
              ${(aiSummary?.accumulated_cost_usd ?? 0.0075).toFixed(4)}
            </span>
          </div>
        </div>
      </div>

      {/* 🕹 SIMULATION PLATFORM PANEL (Hidden in Presentation Mode) */}
      {!presentationMode && (
        <div className="glass-panel rounded-2xl p-5 border border-slate-900 z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-[var(--lime-glow)]" />
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono">Interactive Call Simulator</span>
            </div>

            <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
              <select
                value={selectedFarmer}
                onChange={(e) => setSelectedFarmer(e.target.value)}
                disabled={callActive || isDemoRunning}
                className="bg-slate-950 text-slate-200 border border-slate-900 rounded-xl px-4 py-2 text-xs focus:outline-none focus:border-[var(--lime-glow)] min-w-[240px] disabled:opacity-40 select-none cursor-pointer"
                aria-label="Select farmer profile for simulation"
              >
                <option value="">Select a demographic farmer...</option>
                {demoFarmers.map((f) => (
                  <option key={f.farmer_id} value={f.farmer_id}>
                    {f.name} — {f.category}, {f.district} ({f.land_hectares} ha)
                  </option>
                ))}
              </select>

              <button
                onClick={() => handleSimulateCall(selectedFarmer)}
                disabled={!selectedFarmer || callActive || isDemoRunning}
                className="px-4 py-2 bg-gradient-to-r from-[var(--lime-glow)] to-emerald-500 text-slate-950 rounded-xl text-xs font-black uppercase tracking-wider hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer shrink-0"
              >
                <Play className="w-3 h-3 fill-current" />
                Simulate Ingress
              </button>

              <div className="h-6 w-px bg-slate-900 hidden sm:block" />

              <button
                onClick={handleStartDemo}
                disabled={isDemoRunning || callActive}
                className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 rounded-xl text-xs font-black uppercase tracking-wider hover:shadow-lg hover:shadow-amber-500/10 transition-all duration-300 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer shrink-0"
              >
                {isDemoRunning ? (
                  <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Simulating...</>
                ) : (
                  <><Zap className="w-3.5 h-3.5" /> Full Pipeline Run</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🧭 1. INTERACTIVE WORKFLOW CANVAS (Task 1) */}
      <div className="glass-panel rounded-2xl p-5 overflow-hidden z-10">
        <div className="flex items-center gap-2 mb-5">
          <Layers className="w-4 h-4 text-[var(--lime-glow)]" />
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest font-mono">Operations Workflow Canvas</span>
        </div>

        {/* Responsive Grid mapping stages */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-9 gap-3">
          {workflowStages.map((stage, idx) => {
            const status = getStageStatus(idx);
            const isRunning = status === "Running";
            const isCompleted = status === "Completed";
            const isFailed = status === "Failed";

            return (
              <div
                key={stage.key}
                tabIndex={0}
                aria-label={`Step ${idx + 1}: ${stage.label}, status: ${status}`}
                className={`glass-panel border-2 rounded-2xl p-4 flex flex-col justify-between items-center text-center transition-all duration-300 relative ${
                  reducedMotion ? "" : "hover:-translate-y-1 hover:shadow-md"
                } ${statusColors[status]}`}
              >
                {/* Step indicator */}
                <span className="absolute top-2 left-2 text-[9px] font-bold font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/50 border border-white/5">
                  0{idx + 1}
                </span>

                {/* Pulsing indicator light */}
                {isRunning && (
                  <span className="absolute top-2 right-2 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--sky-agri)] opacity-75" />
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[var(--sky-agri)]" />
                  </span>
                )}

                <div className={`p-3 rounded-xl mb-3 ${
                  isCompleted ? "bg-[var(--lime-glow)]/10" :
                  isRunning ? "bg-[var(--sky-agri)]/10 animate-pulse" :
                  isFailed ? "bg-red-500/10" : "bg-slate-900"
                }`}>
                  {stage.icon}
                </div>

                <div className="w-full">
                  <h4 className={`font-bold tracking-tight text-slate-200 ${presentationMode ? "text-sm" : "text-[11px]"}`}>
                    {stage.label}
                  </h4>
                  <p className="text-[9px] text-slate-500 leading-tight mt-1 truncate" title={stage.desc}>
                    {stage.desc}
                  </p>
                </div>

                <span className={`text-[8px] font-bold uppercase tracking-widest px-2 py-0.5 rounded mt-3 ${
                  isCompleted ? "bg-emerald-500/10 text-emerald-400" :
                  isRunning ? "bg-[var(--sky-agri)]/15 text-[var(--sky-agri)] animate-pulse" :
                  isFailed ? "bg-red-500/15 text-red-400" : "bg-slate-900 text-slate-500"
                }`}>
                  {status}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── CENTRALIZED OPERATION CENTRE WORKSPACE GRID ─────────────────────────── */}
      <div className={`grid grid-cols-1 gap-6 ${presentationMode ? "xl:grid-cols-2" : "xl:grid-cols-3"}`}>
        
        {/* COLUMN 1: DIGITAL TWIN PROFILE CARD (Task 3) */}
        <div className="flex flex-col gap-6">
          <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                <div className="flex items-center gap-2.5">
                  <User className="w-4 h-4 text-teal-400" />
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">Farmer Digital Twin</span>
                </div>
                {farmer?.digital_twin_version && (
                  <span className="text-[9px] font-mono font-black bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2 py-0.5 rounded-lg">
                    v{farmer.digital_twin_version}
                  </span>
                )}
              </div>

              {farmer ? (
                <div className="flex flex-col gap-4">
                  {/* completeness SVG gauge */}
                  <div className="flex items-center gap-4 p-3.5 bg-slate-950/40 border border-slate-900 rounded-2xl">
                    <div className="relative w-14 h-14 flex items-center justify-center shrink-0">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="28" cy="28" r={radius} stroke="#1e293b" strokeWidth="3" fill="transparent" />
                        <circle 
                          cx="28" 
                          cy="28" 
                          r={radius} 
                          stroke="#10b981" 
                          strokeWidth="3.5" 
                          fill="transparent" 
                          strokeDasharray={circumference} 
                          strokeDashoffset={offset}
                          className="transition-all duration-750 ease-out"
                        />
                      </svg>
                      <span className="absolute text-[10px] font-black text-slate-200 font-mono">{completeness}%</span>
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-200">Completeness Ratio</h4>
                      <p className="text-[10px] text-slate-500 mt-0.5 font-medium font-mono">Demographic verification match</p>
                    </div>
                  </div>

                  {/* Upgraded Parameters lists */}
                  <div className="grid grid-cols-2 gap-3 text-[11px] font-semibold font-mono">
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Farmer Name</span>
                      <span className="text-slate-200 block mt-0.5">{farmer.name}</span>
                    </div>
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Social Category</span>
                      <span className="text-amber-400 block mt-0.5">{farmer.category || "Marginal"}</span>
                    </div>
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Landholding</span>
                      <span className="text-slate-200 block mt-0.5">{farmer.land_hectares} Hectares</span>
                    </div>
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">soil profile</span>
                      <span className="text-slate-200 block mt-0.5 truncate">{farmer.district}, {farmer.state}</span>
                    </div>
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Risk profile</span>
                      <span className="text-red-400 block mt-0.5 uppercase tracking-wide">
                        {farmer.risk_profile || "Normal"}
                      </span>
                    </div>
                    <div className="bg-slate-950/40 border border-slate-900/60 p-2.5 rounded-xl">
                      <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Recent Interactions</span>
                      <span className="text-sky-400 block mt-0.5">
                        {farmer.last_interaction || "05-Jul-2026"}
                      </span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider font-mono mb-1.5">Cultivated Crops</span>
                    <div className="flex flex-wrap gap-1.5">
                      {farmer.crops?.map((crop) => (
                        <span key={crop} className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 uppercase font-mono">
                          {crop}
                        </span>
                      )) || <span className="text-slate-650 italic text-[10px]">None registered</span>}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-[10px] text-slate-600 italic">
                  Twin profile loads on call ingress...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* COLUMN 2: REAL-TIME AI THINKING TIMELINE (Task 2) */}
        <div className="flex flex-col gap-6">
          <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                <div className="flex items-center gap-2.5">
                  <Brain className="w-4 h-4 text-indigo-400" />
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">AI Thinking Timeline</span>
                </div>
                {topSchemeName && (
                  <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded truncate max-w-[140px]">
                    {topSchemeName}
                  </span>
                )}
              </div>

              {/* Real-time Timeline List */}
              <div 
                ref={timelineScrollRef}
                className="flex flex-col gap-3 max-h-[340px] overflow-y-auto pr-1 mc-scrollbar relative pl-3.5 border-l border-slate-900/60 ml-2.5"
              >
                {timelineEvents.length > 0 ? (
                  timelineEvents.map((evt, idx) => (
                    <div key={idx} className="relative py-1 flex flex-col gap-1 font-mono text-[10px]">
                      {/* Ring indicator */}
                      <span className={`absolute -left-[20px] top-2.5 w-2 h-2 rounded-full border ${
                        evt.status === "failed" ? "bg-red-500 border-red-400" :
                        evt.status === "pending" ? "bg-amber-500 border-amber-400 animate-pulse" :
                        "bg-emerald-500 border-emerald-400"
                      }`} />
                      
                      <div className="flex justify-between text-[8px] text-slate-500">
                        <span>{evt.timestamp}</span>
                        <span>Lat: {evt.duration} · Conf: {evt.confidence}</span>
                      </div>

                      <div className={`p-2.5 bg-slate-950/45 border border-slate-900 rounded-xl ${
                        evt.status === "failed" ? "text-red-400" :
                        evt.status === "pending" ? "text-amber-400 animate-pulse" :
                        "text-slate-200"
                      }`}>
                        {evt.event}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-16 text-center text-[10px] text-slate-650 italic">
                    Pipeline idle. Ingestion logs stream in dynamically...
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* COLUMN 3: LIVE TELEMETRY HUBS (Task 4) */}
        {!presentationMode && (
          <div className="flex flex-col gap-6">
            <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
              <div>
                <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                  <div className="flex items-center gap-2.5">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">Live Telemetry Gateway</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
                  {/* Telemetry nodes */}
                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Server className="w-3.5 h-3.5 text-sky-400" />
                      <span className="font-bold text-slate-300">FastAPI</span>
                    </div>
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="font-bold text-slate-300">PostgreSQL</span>
                    </div>
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Network className="w-3.5 h-3.5 text-pink-400" />
                      <span className="font-bold text-slate-300">Redis Cache</span>
                    </div>
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Compass className="w-3.5 h-3.5 text-purple-400" />
                      <span className="font-bold text-slate-300">ChromaDB</span>
                    </div>
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between col-span-2">
                    <div className="flex items-center gap-2">
                      <Wifi className={`w-3.5 h-3.5 ${isConnected ? "text-emerald-400" : "text-red-400"}`} />
                      <span className="font-bold text-slate-300">WebSocket Bus</span>
                    </div>
                    <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase ${
                      isConnected ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400 animate-pulse"
                    }`}>{isConnected ? "Connected" : "Offline"}</span>
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div>
                      <span className="text-[8px] text-slate-500 uppercase block font-bold">Calls Active</span>
                      <span className="text-slate-200 mt-1 block font-bold">{calls.filter(c => c.status !== "completed").length} call</span>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-950/40 border border-slate-900/60 rounded-xl flex items-center justify-between">
                    <div>
                      <span className="text-[8px] text-slate-500 uppercase block font-bold">Clients Sub</span>
                      <span className="text-slate-200 mt-1 block font-bold">{clientCount} clients</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>

      {/* ── LOWER LAYER SPECIFIC ADVISOR & AUDIO SYNTHESIS SUMMARY ──────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* MATCHED REGISTRY SCHEMES */}
        <div className="xl:col-span-1 flex flex-col gap-6">
          <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                <div className="flex items-center gap-2.5">
                  <Building2 className="w-4 h-4 text-purple-400" />
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">Matched Registry Schemes</span>
                </div>
                <span className="text-[9px] font-bold text-slate-500 font-mono">{schemes.length} evaluated</span>
              </div>

              {schemes.length > 0 ? (
                <div className="flex flex-col gap-2.5 max-h-[220px] overflow-y-auto pr-1 mc-scrollbar">
                  {schemes.map((s, i) => (
                    <div key={i} className="flex items-center justify-between p-3 bg-slate-950/50 border border-slate-900 rounded-xl hover:border-slate-800 transition font-mono">
                      <div className="flex-1 min-w-0 pr-2">
                        <p className="text-[10px] font-bold text-slate-200 truncate">{s.title}</p>
                        {s.benefits && <p className="text-[9px] text-emerald-400 mt-0.5 font-bold">{s.benefits}</p>}
                      </div>
                      <div className="flex items-center gap-2 ml-2 shrink-0">
                        <span className="text-[10px] text-slate-400 font-bold">{(s.confidence * 100).toFixed(0)}%</span>
                        <StatusBadge status={s.status} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-[10px] text-slate-650 italic">
                  {aiState === "SCHEME_SEARCH_STARTED" || aiState === "SCHEME_EVALUATING" ? (
                    <span className="flex items-center justify-center gap-2 text-amber-400">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Querying registries...
                    </span>
                  ) : "Matched welfare programs load dynamically."}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* CHECKS & PAPERS ADVISOR */}
        <div className="xl:col-span-1 flex flex-col gap-6">
          <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-orange-400" />
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">Checklist Advisor</span>
                </div>
              </div>

              {documentGuidance ? (
                <div className="flex flex-col gap-3 text-[10px] font-semibold font-mono">
                  <div>
                    <span className="text-slate-500 uppercase block font-bold text-[8px] mb-2 tracking-wider">Required Papers</span>
                    <div className="flex flex-wrap gap-1.5">
                      {documentGuidance.required_documents.map((doc, idx) => (
                        <span key={idx} className="bg-slate-950 border border-slate-900 text-slate-300 px-2 py-0.5 rounded flex items-center gap-1.5" title={doc.description}>
                          <CheckCircle2 className={`w-3 h-3 ${doc.status === "available" ? "text-emerald-500" : "text-amber-500"}`} /> {doc.name}
                        </span>
                      ))}
                    </div>
                  </div>

                  {documentGuidance.missing_documents?.length > 0 && (
                    <div className="border-t border-slate-900 pt-2.5">
                      <span className="text-red-400 uppercase block font-bold text-[8px] mb-2 tracking-wider">Missing Action Items</span>
                      <div className="flex flex-wrap gap-1.5">
                        {documentGuidance.missing_documents.map((doc, idx) => (
                          <span key={idx} className="bg-red-500/5 border border-red-500/15 text-red-400 px-2 py-0.5 rounded flex items-center gap-1.5">
                            <AlertCircle className="w-3.5 h-3.5" /> {doc}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="border-t border-slate-900 pt-2.5 grid grid-cols-2 gap-2">
                    <div className="bg-slate-950 p-2 border border-slate-900 rounded-xl">
                      <span className="text-[8px] text-slate-500 block uppercase font-bold">Registry Office</span>
                      <span className="text-slate-200 truncate block mt-0.5">{documentGuidance.nearest_office}</span>
                    </div>
                    <div className="bg-slate-950 p-2 border border-slate-900 rounded-xl">
                      <span className="text-[8px] text-slate-500 block uppercase font-bold">Helpline</span>
                      <span className="text-emerald-400 font-bold block mt-0.5">{documentGuidance.helpline}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 text-center text-[10px] text-slate-650 italic">
                  Registry document checklists evaluate dynamically.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* AUDIO SYNTHESIS SUMMARY SUMMARY */}
        <div className="xl:col-span-1 flex flex-col gap-6">
          <div className="glass-panel rounded-3xl p-5 border border-slate-900 flex-1 flex flex-col justify-between z-10">
            <div>
              <div className="flex items-center justify-between pb-3.5 border-b border-slate-900 mb-4">
                <div className="flex items-center gap-2.5">
                  <Volume2 className="w-4 h-4 text-pink-400" />
                  <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest font-mono">Audio Synthesis Script</span>
                </div>
              </div>

              {voiceText ? (
                <div className="bg-slate-950/50 border border-pink-500/15 rounded-xl p-3.5">
                  <p className="text-[11px] text-slate-200 leading-relaxed italic">&ldquo;{voiceText}&rdquo;</p>
                </div>
              ) : (
                <div className="py-10 text-center text-[10px] text-slate-650 italic">
                  Advisory speech text compiles at final generation step.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Helpers
   ═══════════════════════════════════════════════════════════════════════════ */

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ELIGIBLE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm",
    POSSIBLY_ELIGIBLE: "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-sm",
    NEED_MORE_INFO: "bg-sky-500/10 text-sky-400 border-sky-500/20 shadow-sm animate-pulse",
    NOT_ELIGIBLE: "bg-red-500/10 text-red-400 border-red-500/20 shadow-sm",
  };
  const icons: Record<string, React.ReactNode> = {
    ELIGIBLE: <CheckCircle2 className="w-3 h-3" />,
    POSSIBLY_ELIGIBLE: <AlertCircle className="w-3 h-3" />,
    NEED_MORE_INFO: <Clock className="w-3 h-3 animate-pulse" />,
    NOT_ELIGIBLE: <XCircle className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-bold border capitalize transition-all duration-300 ${colors[status] || "bg-slate-800 text-slate-300 border-slate-700"}`}>
      {icons[status]}
      {status.replace(/_/g, " ").toLowerCase()}
    </span>
  );
}
