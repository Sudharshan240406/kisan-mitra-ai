"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Phone,
  Mic,
  User,
  Building2,
  ClipboardCheck,
  Brain,
  BookOpen,
  TrendingUp,
  FileText,
  MapPin,
  Volume2,
  Play,
  RefreshCw,
  Zap,
  Shield,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronDown,
  Wifi,
  WifiOff,
  Layers
} from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";

/* ═══════════════════════════════════════════════════════════════════════════
   Types
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

interface DocumentGuidance {
  scheme_id: string;
  required_documents: string[];
  missing_documents: string[];
  tips: string[];
  nearest_office: string;
  helpline: string;
  application_steps: string[];
}

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════════════════════ */

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ELIGIBLE: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    POSSIBLY_ELIGIBLE: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    NEED_MORE_INFO: "bg-sky-500/20 text-sky-400 border-sky-500/30",
    NOT_ELIGIBLE: "bg-red-500/20 text-red-400 border-red-500/30",
  };
  const icons: Record<string, React.ReactNode> = {
    ELIGIBLE: <CheckCircle2 className="w-3 h-3" />,
    POSSIBLY_ELIGIBLE: <AlertCircle className="w-3 h-3" />,
    NEED_MORE_INFO: <Clock className="w-3 h-3" />,
    NOT_ELIGIBLE: <XCircle className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${colors[status] || "bg-slate-700 text-slate-300 border-slate-600"}`}>
      {icons[status]}
      {status.replace(/_/g, " ")}
    </span>
  );
}

function PanelCard({ icon, title, badge, children, className = "" }: {
  icon: React.ReactNode;
  title: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`mc-panel bg-slate-900/50 border border-slate-800/60 rounded-2xl overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/40 bg-slate-900/30">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">{title}</span>
        </div>
        {badge}
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════════════ */

export default function MissionControl() {
  // WebSocket
  const { events, lastEvent, isConnected, clientCount } = useWebSocket({
    url: "ws://localhost:8000/ws/live",
  });

  // State
  const [callActive, setCallActive] = useState(false);
  const [callId, setCallId] = useState("");
  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [schemes, setSchemes] = useState<SchemeResult[]>([]);
  const [reasoning, setReasoning] = useState<string[]>([]);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [confidence, setConfidence] = useState(0);
  const [voiceText, setVoiceText] = useState("");
  const [aiState, setAiState] = useState("IDLE");
  const [demoFarmers, setDemoFarmers] = useState<FarmerProfile[]>([]);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [selectedFarmer, setSelectedFarmer] = useState<string>("");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [topSchemeName, setTopSchemeName] = useState<string>("");
  const [documentGuidance, setDocumentGuidance] = useState<DocumentGuidance | null>(null);
  
  // Reconnect count
  const [reconnects, setReconnects] = useState(0);
  
  // Error handling state
  const [errorMsg, setErrorMsg] = useState("");
  const [recoveryAction, setRecoveryAction] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  // Fetch demo farmers on load
  useEffect(() => {
    fetch("http://localhost:8000/api/v1/demo/farmers")
      .then((r) => (r.ok ? r.json() : []))
      .then(setDemoFarmers)
      .catch(() => {});
  }, []);

  // Auto scroll transcript to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript]);

  // Process WebSocket events
  useEffect(() => {
    if (!lastEvent) return;
    const { type, payload } = lastEvent;

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
        break;

      case "DIGITAL_TWIN_LOADED":
        setAiState("DIGITAL_TWIN_LOADED");
        if (payload.digital_twin) {
          setFarmer(payload.digital_twin);
        }
        break;

      case "SCHEME_SEARCH_STARTED":
        setAiState("SCHEME_SEARCH_STARTED");
        setSchemes([]);
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
        break;

      case "ELIGIBILITY_COMPLETED":
        setAiState("ELIGIBILITY_COMPLETED");
        if (payload.results) {
          setSchemes(payload.results);
        }
        break;

      case "REASONING_COMPLETED":
        setAiState("REASONING_COMPLETED");
        setReasoning(payload.reasoning || []);
        setEvidence(payload.evidence || []);
        setConfidence(payload.confidence || 0);
        setTopSchemeName(payload.top_scheme || "");
        break;

      case "DOCUMENT_ADVISOR_READY":
        setAiState("DOCUMENT_ADVISOR_READY");
        setDocumentGuidance(payload as DocumentGuidance);
        break;

      case "VOICE_RESPONSE_STARTED":
        setAiState("VOICE_RESPONSE");
        setVoiceText(payload.text || "");
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
        setTimeout(() => setCallActive(false), 8000);
        break;

      case "CALL_ERROR":
        setAiState("ERROR");
        setErrorMsg(payload.error || "An unexpected call error occurred.");
        setElapsedMs(payload.elapsed_ms || 0);
        break;

      case "ERROR_RECOVERY_STARTED":
        setAiState("ERROR_RECOVERY");
        setRecoveryAction(payload.recovery_action || "escalating");
        setVoiceText(payload.message || "An error occurred, escalating call.");
        break;

      case "DEMO_STARTED":
        setIsDemoRunning(true);
        setAiState("DEMO_RUNNING");
        break;

      case "DEMO_PROGRESS":
        setAiState(`DEMO: Farmer ${payload.current}/${payload.total}`);
        break;

      case "DEMO_COMPLETED":
        setIsDemoRunning(false);
        setAiState("DEMO_COMPLETE");
        break;

      case "MISSION_CONTROL_DISCONNECTED":
        setReconnects((prev) => prev + 1);
        break;

      case "MISSION_CONTROL_RECONNECTED":
        if (payload.reconnect_count !== undefined) {
          setReconnects(payload.reconnect_count);
        }
        break;
        
      case "CONNECTED":
        setAiState("READY");
        break;
    }
  }, [lastEvent]);

  // Handlers
  const handleSimulateCall = async (farmerId: string) => {
    if (!farmerId) return;
    setAiState("CONNECTING");
    try {
      await fetch(`http://localhost:8000/api/v1/demo/simulate-call/${farmerId}`, { method: "POST" });
    } catch {
      setAiState("ERROR");
    }
  };

  const handleStartDemo = async () => {
    setIsDemoRunning(true);
    try {
      await fetch("http://localhost:8000/api/v1/demo/start", { method: "POST" });
    } catch {
      setIsDemoRunning(false);
    }
  };

  const aiStateColor: Record<string, string> = {
    IDLE: "text-slate-500",
    READY: "text-emerald-400 border-emerald-500/20",
    CONNECTING: "text-sky-400 border-sky-500/20",
    CALL_STARTED: "text-emerald-400 border-emerald-500/30 bg-emerald-500/5",
    CALLER_IDENTIFIED: "text-teal-400 border-teal-500/30 bg-teal-500/5",
    DIGITAL_TWIN_LOADED: "text-cyan-400 border-cyan-500/30 bg-cyan-500/5",
    SCHEME_SEARCH_STARTED: "text-amber-400 border-amber-500/30",
    SCHEME_EVALUATING: "text-amber-400 border-amber-500/30 bg-amber-500/5 animate-pulse",
    ELIGIBILITY_COMPLETED: "text-purple-400 border-purple-500/30 bg-purple-500/5",
    REASONING_COMPLETED: "text-indigo-400 border-indigo-500/30 bg-indigo-500/5",
    DOCUMENT_ADVISOR_READY: "text-orange-400 border-orange-500/30 bg-orange-500/5",
    VOICE_RESPONSE: "text-pink-400 border-pink-500/30 bg-pink-500/5",
    CALL_COMPLETED: "text-emerald-400 border-emerald-500/40 bg-emerald-500/10",
    DEMO_RUNNING: "text-amber-500 border-amber-500/30 bg-amber-500/5",
    DEMO_COMPLETE: "text-emerald-400 border-emerald-500/30",
    ERROR: "text-red-400 border-red-500/40 bg-red-500/10",
    ERROR_RECOVERY: "text-red-400 border-red-500/40 bg-red-500/10 animate-pulse",
  };

  // E2E 9-Stage Workflow Canvas States
  const stages = [
    { key: "CALL_STARTED", label: "Call Started" },
    { key: "CALLER_IDENTIFIED", label: "Caller ID" },
    { key: "DIGITAL_TWIN_LOADED", label: "Digital Twin" },
    { key: "SCHEME_SEARCH_STARTED", label: "Scheme Search" },
    { key: "SCHEME_EVALUATING", label: "Evaluating" },
    { key: "REASONING_COMPLETED", label: "AI Reasoning" },
    { key: "DOCUMENT_ADVISOR_READY", label: "Docs Ready" },
    { key: "VOICE_RESPONSE", label: "Voice Playback" },
    { key: "CALL_COMPLETED", label: "Completed" },
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

  const activeStageIndex = getStageIndex(aiState);

  return (
    <div className="flex flex-col gap-5">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-100 flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            Mission Control — Live Operations
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Government Scheme Intelligence Platform • Real-time Telephony & Reasoning Dashboard
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Reconnect Metrics */}
          {reconnects > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-amber-500/20 bg-amber-500/5 text-[10px] font-bold text-amber-400 uppercase tracking-wider">
              <RefreshCw className="w-3 h-3 animate-spin" />
              Reconnects: {reconnects}
            </div>
          )}

          {/* Connection Status */}
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[10px] font-bold uppercase tracking-wider ${
            isConnected
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              : "bg-red-500/10 text-red-400 border-red-500/20"
          }`}>
            {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {isConnected ? `Live Connected (${clientCount})` : "Offline"}
          </div>

          {/* AI State */}
          <div className={`px-3 py-1.5 rounded-full border text-[10px] font-bold uppercase ${aiStateColor[aiState] || "text-slate-400 border-slate-800"}`}>
            AI State: {aiState.replace(/_/g, " ")}
          </div>
        </div>
      </div>

      {/* ── WORKFLOW CANVAS ────────────────────────────────────────────────── */}
      <div className="mc-panel bg-slate-950/40 border border-slate-900 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Workflow Stage Canvas</span>
        </div>
        <div className="grid grid-cols-9 gap-2 relative">
          {stages.map((st, idx) => {
            const isPassed = idx < activeStageIndex;
            const isActive = idx === activeStageIndex;
            
            let bgClass = "bg-slate-900 border-slate-850 text-slate-500";
            if (isPassed) bgClass = "bg-emerald-500/10 border-emerald-500/40 text-emerald-400";
            if (isActive) bgClass = "bg-sky-500/20 border-sky-500/50 text-sky-400 shadow-md shadow-sky-500/5";
            if (aiState.startsWith("ERROR") && isActive) bgClass = "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse";

            return (
              <div key={st.key} className={`flex flex-col items-center p-2 rounded-xl border text-center transition-all ${bgClass}`}>
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold mb-1 border border-current">
                  {isPassed ? "✓" : idx + 1}
                </div>
                <span className="text-[9px] font-semibold uppercase tracking-tight truncate w-full">{st.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Demo Controls */}
      <div className="mc-panel bg-gradient-to-r from-slate-900/80 to-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-emerald-400" />
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Simulate Call</span>
          </div>

          <select
            value={selectedFarmer}
            onChange={(e) => setSelectedFarmer(e.target.value)}
            disabled={callActive || isDemoRunning}
            className="bg-slate-950 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-emerald-500 min-w-[220px] disabled:opacity-40"
          >
            <option value="">Select a demo farmer...</option>
            {demoFarmers.map((f) => (
              <option key={f.farmer_id} value={f.farmer_id}>
                {f.name} — {f.category}, {f.district} ({f.land_hectares}ha)
              </option>
            ))}
          </select>

          <button
            onClick={() => handleSimulateCall(selectedFarmer)}
            disabled={!selectedFarmer || callActive || isDemoRunning}
            className="px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-emerald-500/20 transition-all disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer"
          >
            <Play className="w-3 h-3 fill-current" />
            Simulate Call
          </button>

          <div className="h-6 w-px bg-slate-800" />

          <button
            onClick={handleStartDemo}
            disabled={isDemoRunning || callActive}
            className="px-4 py-1.5 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 rounded-lg text-xs font-bold hover:shadow-lg hover:shadow-amber-500/20 transition-all disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer"
          >
            {isDemoRunning ? (
              <><RefreshCw className="w-3 h-3 animate-spin" /> Demo Running...</>
            ) : (
              <><Zap className="w-3 h-3" /> Full Demo (All Farmers)</>
            )}
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Column 1: Call & Transcript */}
        <div className="flex flex-col gap-4">

          {/* 📞 Live Call / Errors */}
          <PanelCard
            icon={<Phone className="w-4 h-4 text-emerald-400" />}
            title="Live Call Status"
            badge={callActive ? (
              <span className="mc-live-badge flex items-center gap-1 text-[9px] font-bold text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                LIVE
              </span>
            ) : null}
          >
            {errorMsg ? (
              <div className="flex flex-col gap-2 p-2 bg-red-500/10 border border-red-500/25 rounded-xl text-red-400">
                <div className="flex items-center gap-1.5 text-xs font-bold">
                  <AlertCircle className="w-4 h-4" /> Pipeline Error Occurred
                </div>
                <p className="text-[11px] leading-relaxed text-slate-300">{errorMsg}</p>
                {recoveryAction && (
                  <div className="text-[10px] text-amber-400 mt-1 font-semibold">
                    Recovery: {recoveryAction.replace(/_/g, " ")}
                  </div>
                )}
              </div>
            ) : callActive ? (
              <div className="flex flex-col gap-2">
                <div className="text-xs text-slate-300">
                  <span className="text-slate-500">Call ID:</span> <span className="font-mono">{callId}</span>
                </div>
                {farmer && (
                  <>
                    <div className="text-xs text-slate-300">
                      <span className="text-slate-500">Caller:</span> {farmer.name} ({farmer.phone})
                    </div>
                    <div className="text-xs text-slate-300">
                      <span className="text-slate-500">Language:</span> <span className="uppercase text-emerald-400 font-bold">{farmer.language || "Calculating..."}</span>
                    </div>
                  </>
                )}
                {elapsedMs > 0 && (
                  <div className="text-xs text-slate-400">
                    Duration: {(elapsedMs / 1000).toFixed(1)}s
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">No active call. Select a farmer above to begin.</p>
            )}
          </PanelCard>

          {/* 🎙 Live Transcript */}
          <PanelCard
            icon={<Mic className="w-4 h-4 text-sky-400" />}
            title="Live Transcript"
            className="flex-1"
          >
            <div ref={scrollRef} className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-1 mc-scrollbar">
              {transcript.length === 0 ? (
                <p className="text-xs text-slate-600 italic">Waiting for conversation...</p>
              ) : (
                transcript.map((t, i) => (
                  <div key={i} className={`text-xs leading-relaxed rounded-lg px-3 py-2 mc-transcript-in ${
                    t.role === "farmer"
                      ? "bg-sky-500/10 border-l-2 border-sky-500/40 text-slate-200"
                      : t.role === "assistant"
                      ? "bg-emerald-500/10 border-l-2 border-emerald-500/40 text-slate-200"
                      : "bg-slate-800/40 border-l-2 border-slate-700 text-slate-400 text-[10px]"
                  }`}>
                    <div className="flex justify-between items-center mb-0.5">
                      <span className={`font-bold uppercase text-[9px] ${
                        t.role === "farmer" ? "text-sky-400" : t.role === "assistant" ? "text-emerald-400" : "text-slate-500"
                      }`}>
                        {t.role === "farmer" ? "👨‍🌾 Farmer" : t.role === "assistant" ? "🤖 AI Advisor" : "⚙ System"}:
                      </span>
                      <span className="text-[8px] text-slate-600 font-mono">
                        {new Date(t.timestamp * 1000).toLocaleTimeString()}
                      </span>
                    </div>
                    {t.text}
                  </div>
                ))
              )}
            </div>
          </PanelCard>
        </div>

        {/* Column 2: Profile & Schemes */}
        <div className="flex flex-col gap-4">

          {/* 👤 Farmer Digital Twin */}
          <PanelCard
            icon={<User className="w-4 h-4 text-teal-400" />}
            title="Digital Twin Snapshot"
            badge={farmer?.digital_twin_version ? (
              <span className="text-[9px] font-mono font-bold bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2 py-0.5 rounded">
                {farmer.digital_twin_version}
              </span>
            ) : null}
          >
            {farmer ? (
              <div className="flex flex-col gap-3">
                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[11px]">
                  <div><span className="text-slate-500">Name:</span> <span className="text-slate-200 font-semibold">{farmer.name}</span></div>
                  <div><span className="text-slate-500">Category:</span> <span className="text-amber-400 font-semibold">{farmer.category || "N/A"}</span></div>
                  <div><span className="text-slate-500">Land:</span> <span className="text-slate-200">{farmer.land_hectares} ha</span></div>
                  <div><span className="text-slate-500">Gender:</span> <span className="text-slate-200">{farmer.gender}</span></div>
                  <div><span className="text-slate-500">Crops:</span> <span className="text-emerald-400">{farmer.crops?.join(", ")}</span></div>
                  <div><span className="text-slate-500">Caste:</span> <span className="text-slate-200">{farmer.caste || "N/A"}</span></div>
                  <div><span className="text-slate-500">District:</span> <span className="text-slate-200">{farmer.district}</span></div>
                  <div><span className="text-slate-500">State:</span> <span className="text-slate-200">{farmer.state}</span></div>
                </div>
                
                {/* Advanced Digital Twin Metrics */}
                {farmer.profile_completeness !== undefined && (
                  <div className="border-t border-slate-800/60 pt-2 flex flex-col gap-1.5 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Profile Completeness:</span>
                      <span className="text-emerald-400 font-bold">{farmer.profile_completeness}%</span>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-1">
                      <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${farmer.profile_completeness}%` }} />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 mt-1">
                      <div className="bg-slate-950/40 p-1.5 rounded-lg border border-slate-850">
                        <span className="text-[8px] text-slate-500 block uppercase font-bold">Risk Profile</span>
                        <span className={`text-[10px] font-bold ${
                          farmer.risk_profile === "HIGH" ? "text-red-400" :
                          farmer.risk_profile === "MEDIUM" ? "text-amber-400" :
                          "text-emerald-400"
                        }`}>{farmer.risk_profile || "LOW"}</span>
                      </div>
                      <div className="bg-slate-950/40 p-1.5 rounded-lg border border-slate-850">
                        <span className="text-[8px] text-slate-500 block uppercase font-bold">Frequency</span>
                        <span className="text-[10px] text-slate-300 font-semibold">{farmer.last_interaction || "New Farmer"}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Farmer Digital Twin will load when call begins.</p>
            )}
          </PanelCard>

          {/* 🏛 Government Schemes Evaluation */}
          <PanelCard
            icon={<Building2 className="w-4 h-4 text-purple-400" />}
            title="Government Schemes Eligibility"
            badge={<span className="text-[9px] font-mono text-slate-500">{schemes.length} schemes</span>}
          >
            {schemes.length > 0 ? (
              <div className="flex flex-col gap-1.5 max-h-[220px] overflow-y-auto pr-1 mc-scrollbar">
                {schemes.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-slate-950/60 border border-slate-850/60 rounded-xl mc-timeline-item">
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold text-slate-200 truncate">{s.title}</p>
                      {s.benefits && <p className="text-[9px] text-emerald-400 mt-0.5 font-medium">{s.benefits}</p>}
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className="text-[9px] font-mono font-bold text-slate-500">{(s.confidence * 100).toFixed(0)}%</span>
                      <StatusBadge status={s.status} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">
                {aiState === "SCHEME_SEARCH_STARTED" || aiState === "SCHEME_EVALUATING" ? (
                  <span className="flex items-center gap-2 text-amber-400">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Querying government registries...
                  </span>
                ) : "Scheme results will appear after eligibility check."}
              </p>
            )}
          </PanelCard>
        </div>

        {/* Column 3: Reasoning & Documents */}
        <div className="flex flex-col gap-4">

          {/* 🧠 Chief Reasoning Agent */}
          <PanelCard
            icon={<Brain className="w-4 h-4 text-indigo-400" />}
            title="Chief Reasoning Engine"
            badge={topSchemeName ? (
              <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded truncate max-w-[120px]">
                {topSchemeName}
              </span>
            ) : null}
          >
            {reasoning.length > 0 ? (
              <div className="flex flex-col gap-1 max-h-[145px] overflow-y-auto pr-1 mc-scrollbar">
                {reasoning.map((r, i) => (
                  <div key={i} className={`text-[10px] leading-normal px-2.5 py-1 rounded-lg border transition-all ${
                    r.includes("passes") || r.includes("Eligible") || r.startsWith("✓") ? "text-emerald-400 bg-emerald-500/5 border-emerald-500/10" :
                    r.includes("fails") || r.includes("ineligible") || r.startsWith("✗") ? "text-red-400 bg-red-500/5 border-red-500/10" :
                    "text-slate-400 bg-slate-950/20 border-slate-900"
                  }`}>
                    {r}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Chief Reasoning Agent pipeline status will appear here.</p>
            )}
          </PanelCard>

          {/* 📄 Document Advisor Panel */}
          <PanelCard
            icon={<FileText className="w-4 h-4 text-orange-400" />}
            title="Document Advisor Checklist"
          >
            {documentGuidance ? (
              <div className="flex flex-col gap-2 text-[10px]">
                <div>
                  <span className="text-slate-500 uppercase tracking-wider block font-bold text-[8px] mb-1">Required Documents</span>
                  <div className="flex flex-wrap gap-1.5">
                    {documentGuidance.required_documents.map((doc, idx) => (
                      <span key={idx} className="bg-slate-950/80 border border-slate-800 text-slate-300 px-2 py-0.5 rounded flex items-center gap-1 font-medium">
                        <CheckCircle2 className="w-2.5 h-2.5 text-emerald-500" /> {doc}
                      </span>
                    ))}
                  </div>
                </div>

                {documentGuidance.missing_documents && documentGuidance.missing_documents.length > 0 && (
                  <div className="border-t border-slate-800/60 pt-2">
                    <span className="text-red-400 uppercase tracking-wider block font-bold text-[8px] mb-1">Missing / Unverified Docs</span>
                    <div className="flex flex-wrap gap-1.5">
                      {documentGuidance.missing_documents.map((doc, idx) => (
                        <span key={idx} className="bg-red-500/5 border border-red-500/20 text-red-400 px-2 py-0.5 rounded flex items-center gap-1 font-medium">
                          <AlertCircle className="w-2.5 h-2.5" /> {doc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t border-slate-800/60 pt-2 grid grid-cols-2 gap-2">
                  <div className="bg-slate-950/40 p-1.5 rounded-lg border border-slate-850">
                    <span className="text-[8px] text-slate-500 block uppercase font-bold">Nearest Office</span>
                    <span className="text-[10px] text-slate-300 truncate block font-medium" title={documentGuidance.nearest_office}>{documentGuidance.nearest_office}</span>
                  </div>
                  <div className="bg-slate-950/40 p-1.5 rounded-lg border border-slate-850">
                    <span className="text-[8px] text-slate-500 block uppercase font-bold">Helpline Assistance</span>
                    <span className="text-[10px] text-emerald-400 font-bold block">{documentGuidance.helpline}</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">Document Advisor checklist will load once a matching scheme is selected.</p>
            )}
          </PanelCard>

          {/* 🎙 Voice Response & Output */}
          <PanelCard
            icon={<Volume2 className="w-4 h-4 text-pink-400" />}
            title="TTS Voice Summary Output"
          >
            {voiceText ? (
              <div className="bg-slate-950/60 border border-pink-500/20 rounded-xl p-3 mc-timeline-item">
                <p className="text-xs text-slate-200 leading-relaxed italic">&ldquo;{voiceText}&rdquo;</p>
              </div>
            ) : (
              <p className="text-xs text-slate-600 italic">TTS voice summary output text will render here.</p>
            )}
          </PanelCard>
        </div>
      </div>

      {/* Event Timeline */}
      <PanelCard
        icon={<Clock className="w-4 h-4 text-slate-400" />}
        title="Event Stream Timeline"
        badge={<span className="text-[9px] text-slate-500 font-mono">{events.length} events logged</span>}
      >
        <div className="flex gap-2 overflow-x-auto pb-2 mc-scrollbar">
          {events.slice(0, 25).map((evt, i) => (
            <div key={i} className="flex-shrink-0 px-3 py-2 bg-slate-950/60 border border-slate-850/60 rounded-xl min-w-[150px] mc-timeline-item">
              <p className="text-[9px] font-bold text-emerald-400 uppercase tracking-tight">{evt.type.replace(/_/g, " ")}</p>
              <p className="text-[8px] text-slate-500 mt-1 font-mono">
                {new Date(evt.timestamp * 1000).toLocaleTimeString()}
              </p>
            </div>
          ))}
          {events.length === 0 && (
            <p className="text-[10px] text-slate-600 italic">WebSocket events will stream here during calls.</p>
          )}
        </div>
      </PanelCard>
    </div>
  );
}
