"use client";

import React, { useState, useEffect, useRef } from "react";
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
  Check
} from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";

/* ═══════════════════════════════════════════════════════════════════════════
   Types & Interfaces
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

/* ═══════════════════════════════════════════════════════════════════════════
   Sub-components
   ═══════════════════════════════════════════════════════════════════════════ */

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ELIGIBLE: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-sm shadow-emerald-500/5",
    POSSIBLY_ELIGIBLE: "bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-sm shadow-amber-500/5",
    NEED_MORE_INFO: "bg-sky-500/10 text-sky-400 border-sky-500/20 shadow-sm shadow-sky-500/5",
    NOT_ELIGIBLE: "bg-red-500/10 text-red-400 border-red-500/20 shadow-sm shadow-red-500/5",
  };
  const icons: Record<string, React.ReactNode> = {
    ELIGIBLE: <CheckCircle2 className="w-3.5 h-3.5" />,
    POSSIBLY_ELIGIBLE: <AlertCircle className="w-3.5 h-3.5" />,
    NEED_MORE_INFO: <Clock className="w-3.5 h-3.5 animate-pulse" />,
    NOT_ELIGIBLE: <XCircle className="w-3.5 h-3.5" />,
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[10px] font-bold border capitalize transition-all duration-300 ${colors[status] || "bg-slate-800 text-slate-300 border-slate-700"}`}>
      {icons[status]}
      {status.replace(/_/g, " ").toLowerCase()}
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
    <div className={`glass-card rounded-2xl overflow-hidden flex flex-col ${className}`}>
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-900 bg-slate-950/20">
        <div className="flex items-center gap-2.5">
          {icon}
          <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">{title}</span>
        </div>
        {badge}
      </div>
      <div className="p-5 flex-1 flex flex-col justify-between gap-4">
        {children}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   Main Operations Center Component
   ═══════════════════════════════════════════════════════════════════════════ */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export default function MissionControl() {
  // WebSocket setup
  const { lastEvent, isConnected, clientCount, reconnectCount } = useWebSocket({
    url: `${WS_BASE}/ws/live`,
  });

  // Simulator states
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
  const [reconnects, setReconnects] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const [recoveryAction, setRecoveryAction] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  // Load demo farmers
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/demo/farmers`)
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

  // Sync reconnectCount
  useEffect(() => {
    if (reconnectCount > 0) {
      setReconnects(reconnectCount);
    }
  }, [reconnectCount]);

  // Handle WebSocket Event Routing
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

  // Simulation Triggers
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

  // E2E Pipeline Definition
  const stages = [
    { key: "CALL_STARTED", label: "Ingress", desc: "Call connection received" },
    { key: "CALLER_IDENTIFIED", label: "Caller ID", desc: "Phone number resolved" },
    { key: "DIGITAL_TWIN_LOADED", label: "Digital Twin", desc: "Profile data fetched" },
    { key: "SCHEME_SEARCH_STARTED", label: "Search", desc: "Scheme catalog query" },
    { key: "SCHEME_EVALUATING", label: "Evaluating", desc: "Eligibility score match" },
    { key: "REASONING_COMPLETED", label: "AI Logic", desc: "LangGraph reasoning compilation" },
    { key: "DOCUMENT_ADVISOR_READY", label: "Docs Checklist", desc: "Paperwork verify check" },
    { key: "VOICE_RESPONSE", label: "Voice TTS", desc: "Vernacular speech response" },
    { key: "CALL_COMPLETED", label: "Completed", desc: "Session archived" },
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

  const aiStateColor: Record<string, string> = {
    IDLE: "text-slate-500 border-slate-900 bg-slate-950/20",
    READY: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    CONNECTING: "text-sky-400 border-sky-500/20 bg-sky-500/5 animate-pulse",
    CALL_STARTED: "text-emerald-400 border-emerald-500/25 bg-emerald-500/10",
    CALLER_IDENTIFIED: "text-teal-400 border-teal-500/25 bg-teal-500/10",
    DIGITAL_TWIN_LOADED: "text-cyan-400 border-cyan-500/25 bg-cyan-500/10",
    SCHEME_SEARCH_STARTED: "text-amber-400 border-amber-500/20 bg-amber-500/5",
    SCHEME_EVALUATING: "text-amber-400 border-amber-500/25 bg-amber-500/10 animate-pulse",
    ELIGIBILITY_COMPLETED: "text-purple-400 border-purple-500/25 bg-purple-500/10",
    REASONING_COMPLETED: "text-indigo-400 border-indigo-500/25 bg-indigo-500/10",
    DOCUMENT_ADVISOR_READY: "text-orange-400 border-orange-500/25 bg-orange-500/10",
    VOICE_RESPONSE: "text-pink-400 border-pink-500/25 bg-pink-500/10",
    CALL_COMPLETED: "text-emerald-400 border-emerald-500/30 bg-emerald-500/15",
    DEMO_RUNNING: "text-amber-500 border-amber-500/25 bg-amber-500/10",
    DEMO_COMPLETE: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5",
    ERROR: "text-red-400 border-red-500/30 bg-red-500/10",
    ERROR_RECOVERY: "text-red-400 border-red-500/30 bg-red-500/15 animate-pulse",
  };

  // Complete gauge calculation
  const completeness = farmer?.profile_completeness ?? 0;
  const radius = 24;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (completeness / 100) * circumference;

  return (
    <div className="flex flex-col gap-6">
      
      {/* 🧭 HEADER BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-900 pb-5">
        <div>
          <h2 className="text-lg font-black text-slate-100 flex items-center gap-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            Operations Control Center
          </h2>
          <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mt-0.5">
            Vernacular Welfare Intelligence & Real-time Reasoning Bus
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {reconnects > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-amber-500/20 bg-amber-500/5 text-[9px] font-bold text-amber-400 uppercase tracking-wider">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              Reconnects: {reconnects}
            </div>
          )}
          <div className={`px-3 py-1.5 rounded-full border text-[10px] font-bold uppercase tracking-wider transition-all duration-300 ${aiStateColor[aiState] || "text-slate-400 border-slate-800"}`}>
            AI State: {aiState.replace(/_/g, " ")}
          </div>
        </div>
      </div>

      {/* ── 1. INTERACTIVE SVG WORKFLOW PIPELINE ───────────────────────────────── */}
      <div className="glass-panel rounded-2xl p-5 overflow-hidden">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Pipeline Visualization</span>
        </div>
        
        {/* Horizontal scroll container for the SVG flow on small screens */}
        <div className="overflow-x-auto min-w-full mc-scrollbar py-2">
          <div className="min-w-[1100px] relative">
            <svg viewBox="0 0 1080 80" className="w-full h-20 select-none overflow-visible">
              <defs>
                <linearGradient id="passed-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="#059669" stopOpacity="0.3" />
                </linearGradient>
                <linearGradient id="connector-line-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#0ea5e9" />
                </linearGradient>
              </defs>

              {/* Connecting lines */}
              {stages.slice(0, -1).map((_, idx) => {
                const isPassed = idx < activeStageIndex;
                const isActive = idx === activeStageIndex;
                const x1 = idx * 120 + 60;
                const x2 = (idx + 1) * 120 + 60;
                
                let strokeColor = "#1e293b";
                let strokeDash = "0";
                let strokeWidth = "2";
                
                if (isPassed) {
                  strokeColor = "url(#connector-line-grad)";
                  strokeWidth = "3";
                } else if (isActive) {
                  strokeColor = "#0ea5e9";
                  strokeDash = "4 4";
                  strokeWidth = "3";
                }

                return (
                  <line 
                    key={`line-${idx}`}
                    x1={x1} 
                    y1={40} 
                    x2={x2} 
                    y2={40} 
                    stroke={strokeColor} 
                    strokeWidth={strokeWidth}
                    strokeDasharray={strokeDash}
                    className="transition-all duration-500"
                  />
                );
              })}

              {/* Node circles & numbers */}
              {stages.map((st, idx) => {
                const isPassed = idx < activeStageIndex;
                const isActive = idx === activeStageIndex;
                const cx = idx * 120 + 60;
                
                let circleColor = "fill-slate-950 stroke-slate-800";
                let textColor = "fill-slate-500";
                let rSize = 16;
                let ringGlow = "none";

                if (isPassed) {
                  circleColor = "fill-emerald-500/10 stroke-emerald-500";
                  textColor = "fill-emerald-400";
                } else if (isActive) {
                  circleColor = "fill-sky-500/15 stroke-sky-500";
                  textColor = "fill-sky-400";
                  rSize = 19;
                  ringGlow = "drop-shadow(0 0 6px rgba(14, 165, 233, 0.4))";
                }

                if (aiState.startsWith("ERROR") && isActive) {
                  circleColor = "fill-red-500/15 stroke-red-500";
                  textColor = "fill-red-400";
                }

                return (
                  <g key={st.key} className="cursor-pointer group" style={{ filter: ringGlow }}>
                    <circle 
                      cx={cx} 
                      cy={40} 
                      r={rSize} 
                      className={`transition-all duration-300 ${circleColor}`} 
                    />
                    <text 
                      x={cx} 
                      y={43} 
                      textAnchor="middle" 
                      className={`text-[10px] font-black font-mono transition-all duration-300 ${textColor}`}
                    >
                      {isPassed ? "✓" : idx + 1}
                    </text>

                    {/* Stage Label */}
                    <text 
                      x={cx} 
                      y={72} 
                      textAnchor="middle" 
                      className={`text-[9px] font-bold uppercase tracking-wider transition-all duration-300 ${
                        isActive ? "fill-sky-400" : isPassed ? "fill-emerald-400" : "fill-slate-500"
                      }`}
                    >
                      {st.label}
                    </text>

                    {/* Tooltip Hover Area */}
                    <title>{`${st.label}: ${st.desc}`}</title>
                  </g>
                );
              })}
            </svg>
          </div>
        </div>
      </div>

      {/* 🕹 SIMULATION CONTROL HEADER */}
      <div className="glass-card rounded-2xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Phone className="w-4 h-4 text-emerald-400" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Interactive Call Simulator</span>
          </div>

          <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
            <select
              value={selectedFarmer}
              onChange={(e) => setSelectedFarmer(e.target.value)}
              disabled={callActive || isDemoRunning}
              className="bg-slate-950 text-slate-200 border border-slate-900 rounded-xl px-4 py-2 text-xs focus:outline-none focus:border-emerald-500 min-w-[240px] disabled:opacity-40 select-none cursor-pointer"
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
              className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 rounded-xl text-xs font-bold hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer shrink-0"
            >
              <Play className="w-3 h-3 fill-current" />
              Simulate Ingress
            </button>

            <div className="h-6 w-px bg-slate-900 hidden sm:block" />

            <button
              onClick={handleStartDemo}
              disabled={isDemoRunning || callActive}
              className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-slate-950 rounded-xl text-xs font-bold hover:shadow-lg hover:shadow-amber-500/10 transition-all duration-300 disabled:opacity-40 disabled:pointer-events-none flex items-center gap-1.5 cursor-pointer shrink-0"
            >
              {isDemoRunning ? (
                <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Running...</>
              ) : (
                <><Zap className="w-3.5 h-3.5" /> Full Demo Run</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── MAIN OPS GRID ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* COLUMN 1: LIVE CALL & TRANSCRIPT CHAT BUBBLES */}
        <div className="flex flex-col gap-6">
          
          {/* Live Call Telephony Widget */}
          <PanelCard
            icon={<Activity className="w-4 h-4 text-emerald-400" />}
            title="Live Call Telephony Gateway"
            badge={callActive ? (
              <span className="flex items-center gap-1 text-[9px] font-bold text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
                LIVE
              </span>
            ) : null}
          >
            {errorMsg ? (
              <div className="flex flex-col gap-2.5 p-3.5 bg-red-500/5 border border-red-500/15 rounded-xl text-red-400">
                <div className="flex items-center gap-2 text-xs font-bold">
                  <ShieldAlert className="w-4 h-4" /> Pipeline Error Resolved
                </div>
                <p className="text-[10px] leading-relaxed text-slate-400">{errorMsg}</p>
                {recoveryAction && (
                  <div className="text-[9px] text-amber-400 font-bold uppercase tracking-wider">
                    Auto Fallback: {recoveryAction.replace(/_/g, " ")}
                  </div>
                )}
              </div>
            ) : callActive ? (
              <div className="flex flex-col gap-2 font-mono text-[10px] text-slate-400">
                <div className="flex justify-between border-b border-slate-900 pb-1.5">
                  <span className="text-slate-500">Call Reference:</span>
                  <span className="text-slate-200">{callId}</span>
                </div>
                {farmer && (
                  <>
                    <div className="flex justify-between border-b border-slate-900 pb-1.5">
                      <span className="text-slate-500">Caller:</span>
                      <span className="text-slate-200">{farmer.name} ({farmer.phone})</span>
                    </div>
                    <div className="flex justify-between border-b border-slate-900 pb-1.5">
                      <span className="text-slate-500">IVR Language:</span>
                      <span className="text-emerald-400 font-bold uppercase">{farmer.language || "Hi-IN"}</span>
                    </div>
                  </>
                )}
                {elapsedMs > 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Elapsed:</span>
                    <span className="text-slate-300">{(elapsedMs / 1000).toFixed(1)}s</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 text-center text-[10px] text-slate-600 italic">
                Ready for Ingress. Select a farmer above to start.
              </div>
            )}
          </PanelCard>

          {/* Interactive Chat Transcript Bubbles */}
          <PanelCard
            icon={<Mic className="w-4 h-4 text-sky-400" />}
            title="Ingestion Conversation Thread"
            className="flex-1"
          >
            <div ref={scrollRef} className="flex flex-col gap-3.5 max-h-[360px] overflow-y-auto pr-1 mc-scrollbar">
              {transcript.length === 0 ? (
                <div className="py-12 text-center text-[10px] text-slate-650 italic">
                  Thread waiting for ingress dialogue...
                </div>
              ) : (
                transcript.map((t, i) => {
                  const isFarmer = t.role === "farmer";
                  const isAssistant = t.role === "assistant";
                  
                  let bubbleBg = "bg-slate-950/40 border border-slate-900 text-slate-400";
                  let justify = "justify-start";
                  let borderHighlight = "border-l-2 border-l-slate-800";

                  if (isFarmer) {
                    bubbleBg = "bg-sky-500/5 border border-sky-500/10 text-slate-200";
                    justify = "justify-start";
                    borderHighlight = "border-l-2 border-l-sky-500/40";
                  } else if (isAssistant) {
                    bubbleBg = "bg-emerald-500/5 border border-emerald-500/10 text-slate-200";
                    justify = "justify-start";
                    borderHighlight = "border-l-2 border-l-emerald-500/40";
                  }

                  return (
                    <div key={i} className={`flex ${justify} w-full`}>
                      <div className={`rounded-2xl p-3.5 text-[11px] leading-relaxed max-w-[92%] transition-all ${bubbleBg} ${borderHighlight}`}>
                        <div className="flex justify-between items-center gap-4 mb-1">
                          <span className={`text-[9px] font-black uppercase tracking-wider ${
                            isFarmer ? "text-sky-400" : isAssistant ? "text-emerald-400" : "text-slate-500"
                          }`}>
                            {isFarmer ? "👨‍🌾 Farmer Speech" : isAssistant ? "🤖 AI Advisor Synthesis" : "⚙ System Node"}
                          </span>
                          <span className="text-[8px] text-slate-600 font-mono">
                            {new Date(t.timestamp * 1000).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="font-semibold text-slate-200 mt-1">{t.text}</p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </PanelCard>

        </div>

        {/* COLUMN 2: DIGITAL TWIN PROFILE & ELIGIBLE SCHEMES */}
        <div className="flex flex-col gap-6">

          {/* Upgraded Premium Digital Twin */}
          <PanelCard
            icon={<User className="w-4 h-4 text-teal-400" />}
            title="Farmer Digital Twin Profile"
            badge={farmer?.digital_twin_version ? (
              <span className="text-[9px] font-mono font-black bg-teal-500/10 text-teal-400 border border-teal-500/20 px-2 py-0.5 rounded-lg">
                v{farmer.digital_twin_version}
              </span>
            ) : null}
          >
            {farmer ? (
              <div className="flex flex-col gap-5">
                {/* completeness SVG gauge */}
                <div className="flex items-center gap-4 p-3 bg-slate-950/40 border border-slate-900 rounded-2xl">
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
                    <h4 className="text-xs font-bold text-slate-200">Completeness Profile</h4>
                    <p className="text-[10px] text-slate-500 mt-0.5 font-medium">Verified parameters registry</p>
                  </div>
                </div>

                {/* demographic details grid */}
                <div className="grid grid-cols-2 gap-3 text-[11px] font-semibold">
                  <div className="bg-slate-950/40 border border-slate-900 p-2.5 rounded-xl">
                    <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Farmer Name</span>
                    <span className="text-slate-200 block mt-0.5">{farmer.name}</span>
                  </div>
                  <div className="bg-slate-950/40 border border-slate-900 p-2.5 rounded-xl">
                    <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Social Category</span>
                    <span className="text-amber-400 block mt-0.5">{farmer.category || "General"}</span>
                  </div>
                  <div className="bg-slate-950/40 border border-slate-900 p-2.5 rounded-xl">
                    <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Landhold Size</span>
                    <span className="text-slate-200 block mt-0.5">{farmer.land_hectares} Hectares</span>
                  </div>
                  <div className="bg-slate-950/40 border border-slate-900 p-2.5 rounded-xl">
                    <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider">Soil/Location Profile</span>
                    <span className="text-slate-300 block mt-0.5 truncate" title={`${farmer.district}, ${farmer.state}`}>
                      {farmer.district}, {farmer.state}
                    </span>
                  </div>
                </div>

                {/* Crop badges */}
                <div>
                  <span className="text-[8px] font-black text-slate-500 uppercase block tracking-wider mb-1.5">Cultivated Crops</span>
                  <div className="flex flex-wrap gap-1.5">
                    {farmer.crops?.map((crop) => (
                      <span key={crop} className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                        {crop}
                      </span>
                    )) || <span className="text-slate-650 italic text-[10px]">None registered</span>}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-[10px] text-slate-600 italic">
                Digital Twin profile loading on call ingress...
              </div>
            )}
          </PanelCard>

          {/* Upgraded Eligible Schemes */}
          <PanelCard
            icon={<Building2 className="w-4 h-4 text-purple-400" />}
            title="Welfare Registry Matched Schemes"
            badge={<span className="text-[9px] font-bold text-slate-500 font-mono">{schemes.length} evaluated</span>}
          >
            {schemes.length > 0 ? (
              <div className="flex flex-col gap-2.5 max-h-[220px] overflow-y-auto pr-1 mc-scrollbar">
                {schemes.map((s, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-slate-950/60 border border-slate-900 rounded-xl transition hover:border-slate-800">
                    <div className="flex-1 min-w-0 pr-2">
                      <p className="text-[11px] font-semibold text-slate-200 truncate">{s.title}</p>
                      {s.benefits && <p className="text-[9px] text-emerald-400 mt-0.5 font-bold">{s.benefits}</p>}
                    </div>
                    <div className="flex items-center gap-2.5 ml-2 shrink-0">
                      <span className="text-[10px] font-bold text-slate-400 font-mono">{(s.confidence * 100).toFixed(0)}%</span>
                      <StatusBadge status={s.status} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center text-[10px] text-slate-600 italic">
                {aiState === "SCHEME_SEARCH_STARTED" || aiState === "SCHEME_EVALUATING" ? (
                  <span className="flex items-center justify-center gap-2 text-amber-400">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Querying government registries...
                  </span>
                ) : "Registry matches will appear after scheme query step."}
              </div>
            )}
          </PanelCard>

        </div>

        {/* COLUMN 3: REASONING TIMELINE & PAPERWORK CHECKS */}
        <div className="flex flex-col gap-6">

          {/* Upgraded AI Thinking Timeline */}
          <PanelCard
            icon={<Brain className="w-4 h-4 text-indigo-400" />}
            title="Reasoning Engine Graph Timeline"
            badge={topSchemeName ? (
              <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded truncate max-w-[140px]">
                {topSchemeName}
              </span>
            ) : null}
          >
            {reasoning.length > 0 ? (
              <div className="flex flex-col gap-2 max-h-[160px] overflow-y-auto pr-1 mc-scrollbar relative pl-3.5 border-l border-slate-900/60 ml-1.5">
                {reasoning.map((r, i) => {
                  const isSuccess = r.includes("passes") || r.includes("Eligible") || r.startsWith("✓");
                  const isFail = r.includes("fails") || r.includes("ineligible") || r.startsWith("✗");
                  
                  let dotColor = "bg-slate-800 border-slate-900";
                  let textStyle = "text-slate-400";
                  
                  if (isSuccess) {
                    dotColor = "bg-emerald-500 border-emerald-400 shadow-sm shadow-emerald-500/10";
                    textStyle = "text-emerald-400/90 font-bold";
                  } else if (isFail) {
                    dotColor = "bg-red-500 border-red-400 shadow-sm shadow-red-500/10";
                    textStyle = "text-red-400/90 font-bold";
                  }

                  return (
                    <div key={i} className="relative py-0.5">
                      {/* Timeline Dot */}
                      <span className={`absolute -left-[19.5px] top-2 w-2 h-2 rounded-full border ${dotColor}`} />
                      <div className={`text-[10px] leading-relaxed p-2 bg-slate-950/40 border border-slate-900/60 rounded-xl ${textStyle}`}>
                        {r}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="py-12 text-center text-[10px] text-slate-650 italic">
                Reasoning graph nodes compile on eligibility match...
              </div>
            )}
          </PanelCard>

          {/* Upgraded Checklist Advisor */}
          <PanelCard
            icon={<FileText className="w-4 h-4 text-orange-400" />}
            title="Document Checklist Advisor"
          >
            {documentGuidance ? (
              <div className="flex flex-col gap-3 text-[10px] font-semibold">
                <div>
                  <span className="text-slate-500 uppercase tracking-widest block font-bold text-[8px] mb-2">Required Registry Papers</span>
                  <div className="flex flex-wrap gap-1.5">
                    {documentGuidance.required_documents.map((doc, idx) => (
                      <span key={idx} className="bg-slate-950/80 border border-slate-900 text-slate-300 px-2.5 py-1 rounded-lg flex items-center gap-1.5 font-semibold" title={doc.description}>
                        <CheckCircle2 className={`w-3 h-3 ${doc.status === "available" ? "text-emerald-500" : "text-amber-500"}`} /> {doc.name}
                      </span>
                    ))}
                  </div>
                </div>

                {documentGuidance.missing_documents && documentGuidance.missing_documents.length > 0 && (
                  <div className="border-t border-slate-900 pt-2.5">
                    <span className="text-red-400 uppercase tracking-widest block font-bold text-[8px] mb-2">Action Required: Missing Papers</span>
                    <div className="flex flex-wrap gap-1.5">
                      {documentGuidance.missing_documents.map((doc, idx) => (
                        <span key={idx} className="bg-red-500/5 border border-red-500/15 text-red-400 px-2.5 py-1 rounded-lg flex items-center gap-1.5 font-bold">
                          <AlertCircle className="w-3.5 h-3.5" /> {doc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t border-slate-900 pt-2.5 grid grid-cols-2 gap-2 text-[10px]">
                  <div className="bg-slate-950/40 p-2 border border-slate-900 rounded-xl">
                    <span className="text-[8px] text-slate-500 block uppercase font-bold">Nearest Office</span>
                    <span className="text-slate-200 truncate block mt-0.5" title={documentGuidance.nearest_office}>{documentGuidance.nearest_office}</span>
                  </div>
                  <div className="bg-slate-950/40 p-2 border border-slate-900 rounded-xl">
                    <span className="text-[8px] text-slate-500 block uppercase font-bold">Helpline</span>
                    <span className="text-emerald-400 font-bold block mt-0.5">{documentGuidance.helpline}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-[10px] text-slate-605 italic">
                Checks load once a matching scheme is selected.
              </div>
            )}
          </PanelCard>

          {/* Upgraded Voice response summary output */}
          <PanelCard
            icon={<Volume2 className="w-4 h-4 text-pink-400" />}
            title="Audio Synthesis Summary"
          >
            {voiceText ? (
              <div className="bg-slate-950/50 border border-pink-500/15 rounded-xl p-3.5">
                <p className="text-[11px] text-slate-200 leading-relaxed italic">&ldquo;{voiceText}&rdquo;</p>
              </div>
            ) : (
              <div className="py-6 text-center text-[10px] text-slate-650 italic">
                Summary TTS speech text compiles at final step.
              </div>
            )}
          </PanelCard>

        </div>

      </div>

    </div>
  );
}
